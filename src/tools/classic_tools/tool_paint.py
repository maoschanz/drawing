# tool_paint.py

import cairo
from gi.repository import Gtk, Gdk, GdkPixbuf

from .abstract_classic_tool import AbstractClassicTool
from .utilities import utilities_get_magic_path
from .utilities import utilities_get_rgb_for_xy

class ToolPaint(AbstractClassicTool):
	__gtype_name__ = 'ToolPaint'

	def __init__(self, window, **kwargs):
		super().__init__('paint', _("Paint"), 'tool-paint-symbolic', window)
		self.magic_path = None
		self.use_size = False
		self.add_tool_action_enum('paint_algo', 'fill')

	def get_options_label(self):
		return _("Painting options")

	def get_edition_status(self):
		if self.get_option_value('paint_algo') == 'clipping':
			return _("Click on an area to replace its color by transparency")
		else:
			return self.label

	def on_press_on_area(self, event, surface, event_x, event_y):
		self.set_common_values(event.button)

	def on_release_on_area(self, event, surface, event_x, event_y):
		# Guard clause: we can't paint outside of the surface
		if event_x < 0 or event_x > surface.get_width() \
		or event_y < 0 or event_y > surface.get_height():
			return

		(x, y) = (int(event_x), int(event_y))
		self.old_color = utilities_get_rgb_for_xy(surface, x, y)

		if self.get_option_value('paint_algo') == 'fill':
			self.magic_path = utilities_get_magic_path(surface, x, y, self.window, 1)
		elif self.get_option_value('paint_algo') == 'replace':
			self.magic_path = utilities_get_magic_path(surface, x, y, self.window, 2)
		else:
			pass # == 'clipping'

		operation = self.build_operation()
		self.apply_operation(operation)

	############################################################################

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'algo': self.get_option_value('paint_algo'),
			'rgba': self.main_color,
			'old_rgb': self.old_color,
			'path': self.magic_path
		}
		return operation

	def do_tool_operation(self, operation):
		if operation['tool_id'] != self.id:
			return
		self.restore_pixbuf()

		if operation['algo'] == 'replace':
			self.op_replace(operation)
		elif operation['algo'] == 'fill':
			self.op_fill(operation)
		else: # == 'clipping'
			self.op_clipping(operation)

	############################################################################

	def op_replace(self, operation):
		"""Moins laid mais piêtre gestion des couleurs (semi-)transparentes en
		dehors de la zone ciblée."""
		if operation['path'] is None:
			return
		cairo_context = cairo.Context(self.get_surface())
		rgba = operation['rgba']
		old_rgb = operation['old_rgb']
		cairo_context.set_source_rgba(255, 255, 255, 1.0)
		cairo_context.append_path(operation['path'])
		cairo_context.set_operator(cairo.Operator.DEST_IN)
		cairo_context.fill_preserve()

		self.get_image().temp_pixbuf = Gdk.pixbuf_get_from_surface(self.get_surface(), \
			0, 0, self.get_surface().get_width(), self.get_surface().get_height())

		tolerance = 10 # XXX
		i = -1 * tolerance
		while i < tolerance:
			red = max(0, old_rgb[0]+i)
			green = max(0, old_rgb[1]+i)
			blue = max(0, old_rgb[2]+i)
			red = int( min(255, red) )
			green = int( min(255, green) )
			blue = int( min(255, blue) )
			self.get_image().temp_pixbuf = self.get_image().temp_pixbuf.add_alpha(True, red, green, blue)
			i = i+1
		self.restore_pixbuf()
		cairo_context2 = cairo.Context(self.get_surface())

		cairo_context2.append_path(operation['path'])
		cairo_context2.set_operator(cairo.Operator.CLEAR)
		cairo_context2.set_source_rgba(255, 255, 255, 1.0)
		cairo_context2.fill()
		cairo_context2.set_operator(cairo.Operator.OVER)

		Gdk.cairo_set_source_pixbuf(cairo_context2, \
			self.get_image().get_temp_pixbuf(), 0, 0)
		cairo_context2.append_path(operation['path'])
		cairo_context2.paint()
		self.non_destructive_show_modif()
		cairo_context2.set_operator(cairo.Operator.DEST_OVER)
		cairo_context2.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)
		cairo_context2.paint()

	def op_fill(self, operation):
		"""Simple mais laid et reposant sur la précision du path."""
		if operation['path'] is None:
			return
		cairo_context = cairo.Context(self.get_surface())
		rgba = operation['rgba']
		cairo_context.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)
		cairo_context.append_path(operation['path'])
		cairo_context.fill()

	def op_clipping(self, operation):
		"""Remplacement de la couleur par du alpha."""
		old_rgb = operation['old_rgb']
		r0 = old_rgb[0]
		g0 = old_rgb[1]
		b0 = old_rgb[2]
		margin = 0 # TODO as an option ? is not elegant but is powerful
		for i in range(-1 * margin, margin+1):
			r = r0 + i
			if r <= 255 and r >= 0:
				for j in range(-1 * margin, margin+1):
					g = g0 + j
					if g <= 255 and g >= 0:
						for k in range(-1 * margin, margin+1):
							b = b0 + k
							if b <= 255 and b >= 0:
								self.get_image().main_pixbuf = \
								 self.get_main_pixbuf().add_alpha(True, r, g, b)
		self.restore_pixbuf()
		self.non_destructive_show_modif()
