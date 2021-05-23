# tool_paint.py
#
# Copyright 2018-2021 Romain F. T.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import cairo
from gi.repository import Gdk
from .abstract_classic_tool import AbstractClassicTool
from .utilities_paths import utilities_get_magic_path
from .utilities_paths import utilities_get_rgba_for_xy

class ToolPaint(AbstractClassicTool):
	__gtype_name__ = 'ToolPaint'

	def __init__(self, window, **kwargs):
		# Context: the name of a tool to fill an area of one color with an other
		super().__init__('paint', _("Paint"), 'tool-paint-symbolic', window)
		self._magic_path = None
		self.use_size = False
		self.add_tool_action_enum('paint_algo', 'replace')

	def get_options_label(self):
		return _("Painting options")

	def get_edition_status(self):
		paint_algo = self.get_option_value('paint_algo')
		if paint_algo == 'clipping':
			return _("Click on an area to replace its color by transparency")
		elif paint_algo == 'whole':
			return _("Click on the canvas to entirely paint it")
		else:
			return self.label

	def on_press_on_area(self, event, surface, event_x, event_y):
		self.set_common_values(event.button, event_x, event_y)

	def on_release_on_area(self, event, surface, event_x, event_y):
		# Guard clause: we can't paint outside of the surface
		if event_x < 0 or event_x > surface.get_width() \
		or event_y < 0 or event_y > surface.get_height():
			return

		(x, y) = (int(event_x), int(event_y))
		self.old_color = utilities_get_rgba_for_xy(surface, x, y)

		if self.get_option_value('paint_algo') == 'fill':
			self._magic_path = utilities_get_magic_path(surface, x, y, self.window, 1)
		elif self.get_option_value('paint_algo') == 'replace':
			self._magic_path = utilities_get_magic_path(surface, x, y, self.window, 2)
		else:
			pass # == 'clipping' or == 'whole'

		operation = self.build_operation(x, y)
		self.apply_operation(operation)

	############################################################################

	def build_operation(self, x, y):
		operation = {
			'tool_id': self.id,
			'algo': self.get_option_value('paint_algo'),
			# 'x': x,
			# 'y': y,
			'rgba': self.main_color,
			'antialias': self._use_antialias,
			'old_rgba': self.old_color,
			'path': self._magic_path
		}
		return operation

	def do_tool_operation(self, operation):
		self.start_tool_operation(operation) # XXX expose antialiasing option?

		if operation['algo'] == 'replace':
			self._op_replace(operation)
		elif operation['algo'] == 'whole':
			self._op_whole(operation)
		elif operation['algo'] == 'fill':
			self._op_fill(operation)
		else: # == 'clipping'
			self._op_clipping(operation)

	############################################################################

	def _op_whole(self, operation):
		"""Paint the entire image regardless of existing pixels"""
		cairo_context = self.get_context()
		rgba = operation['rgba']
		cairo_context.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)
		cairo_context.paint()

	def _op_fill(self, operation):
		"""Simple but ugly, and it's relying on the precision of the provided
		path whose creation is based on shitty heurisctics."""
		if operation['path'] is None:
			return
		cairo_context = self.get_context()
		rgba = operation['rgba']
		cairo_context.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)
		cairo_context.append_path(operation['path'])
		# can_fill = cairo_context.in_fill(operation['x'], operation['y'])
		# print(can_fill)
		# if not can_fill:
		# 	cairo_context.set_fill_rule(cairo.FillRule.EVEN_ODD)
		# 	XXX doesn't work as i expected
		cairo_context.fill()

	def _op_replace(self, operation):
		"""Algorithmically less ugly than `_op_fill`, but the replacing strategy
		itself doesn't handle (semi-) transparent colors correctly. Looks fine
		when there is no alpha at all and the anti-aliasing is off."""
		# In this example, the user paints in blue and clicks on X (red):
		#
		# rrrrrrrrrrrrrrrrrrrrrrrrr
		# rrrgggggggggggggggggrrXrr
		# rrrgaaaaaaaaaaaaaaagrrrrr
		# rrrgaaaaaaaaaaaaaaagrrrrr
		# rrrgggggggggggggggggrraaa
		# rrrrrrrrrrrrrrrrrrrrrraaa
		#
		# All red pixels will be painted blue, but FIXME all the green ones too.
		if operation['path'] is None:
			return

		# First, everything BUT the targeted area is erased
		surface = self.get_surface()
		cairo_context = cairo.Context(surface)
		rgba = operation['rgba']
		old_rgba = operation['old_rgba']
		cairo_context.set_source_rgba(255, 255, 255, 1.0)
		cairo_context.append_path(operation['path'])
		cairo_context.set_operator(cairo.Operator.DEST_IN)
		cairo_context.set_line_width(4) # ptêt too much mdr
		cairo_context.set_antialias(cairo.Antialias.NONE)
		cairo_context.stroke_preserve()
		# cairo_context.fill_preserve()

		# The result is loaded as the temp pixbuf…
		self.get_image().set_temp_pixbuf(Gdk.pixbuf_get_from_surface(surface, \
		                       0, 0, surface.get_width(), surface.get_height()))
		# …where the targeted color is replaced by pure alpha
		TOLERANCE = 10 # XXX uuugly
		i = -1 * TOLERANCE
		while i < TOLERANCE:
			red = max(0, old_rgba[0]+i)
			green = max(0, old_rgba[1]+i)
			blue = max(0, old_rgba[2]+i)
			red = int(min(255, red))
			green = int(min(255, green))
			blue = int(min(255, blue))
			self._replace_temp_with_alpha(red, green, blue)
			i = i+1

		# The main pixbuf is restored, since its alterations were a side effect
		# of this highly stupid algorithm
		self.restore_pixbuf()
		# We get a context from it again
		cairo_context2 = self.get_context()

		# The content of the path is cleared
		cairo_context2.append_path(operation['path'])
		cairo_context2.set_operator(cairo.Operator.CLEAR)
		cairo_context2.set_source_rgba(255, 255, 255, 1.0)
		cairo_context2.set_line_width(3) # ptêt too much mdr
		cairo_context.set_antialias(cairo.Antialias.NONE)
		cairo_context2.stroke_preserve()
		cairo_context2.fill()

		# The temp pixbuf (where "only" the pixels around the outline which are
		# not in the targeted color still exist) is shown on top of the image
		cairo_context2.set_operator(cairo.Operator.OVER)
		Gdk.cairo_set_source_pixbuf(cairo_context2, \
		                                     self.get_image().temp_pixbuf, 0, 0)
		cairo_context2.paint()
		self.non_destructive_show_modif()

		# The transparent pixels within the path are painted with the new color
		cairo_context2.set_operator(cairo.Operator.DEST_OVER)
		cairo_context2.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)
		cairo_context2.append_path(operation['path'])
		# cairo_context2.paint()
		cairo_context2.set_line_width(3) # ptêt too much mdr
		cairo_context2.stroke_preserve()
		cairo_context2.fill()

	def _op_clipping(self, operation):
		"""Replace the color with transparency by adding an alpha channel."""
		old_rgba = operation['old_rgba']
		r0 = old_rgba[0]
		g0 = old_rgba[1]
		b0 = old_rgba[2]
		# ^ it's not possible to take into account the alpha channel
		margin = 0 # XXX as an option ? is not elegant but it's powerful
		self._clip_red(margin, r0, g0, b0)
		self.restore_pixbuf()
		self.non_destructive_show_modif()

	############################################################################

	def _clip_red(self, margin, r0, g0, b0):
		for i in range(-1 * margin, margin + 1):
			r = r0 + i
			if r <= 255 and r >= 0:
				self._clip_green(margin, r, g0, b0)

	def _clip_green(self, margin, r, g0, b0):
		for i in range(-1 * margin, margin + 1):
			g = g0 + i
			if g <= 255 and g >= 0:
				self._clip_blue(margin, r, g, b0)

	def _clip_blue(self, margin, r, g, b0):
		for i in range(-1 * margin, margin + 1):
			b = b0 + i
			if b <= 255 and b >= 0:
				self._replace_main_with_alpha(r, g, b)

	def _replace_main_with_alpha(self, red, green, blue):
		new_pixbuf = self.get_main_pixbuf().add_alpha(True, red, green, blue)
		self.get_image().set_main_pixbuf(new_pixbuf)

	def _replace_temp_with_alpha(self, red, green, blue):
		new_pixbuf = self.get_image().temp_pixbuf.add_alpha(True, red, green, blue)
		self.get_image().set_temp_pixbuf(new_pixbuf)

	############################################################################
################################################################################
