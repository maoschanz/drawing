# tool_paint.py
#
# Copyright 2018-2023 Romain F. T.
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
from .abstract_classic_tool import AbstractClassicTool
from .utilities_paths import utilities_get_magic_path

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

	def get_editing_tips(self):
		paint_algo = self.get_option_value('paint_algo')
		if paint_algo == 'clipping':
			return [_("Click on an area to replace its color by transparency")]
		elif paint_algo == 'whole':
			return [_("Click on the canvas to entirely paint it")]

		label_warning1 = self.label + " - " + _("May not work for complex shapes")
		label_warning2 = self.label + " - " + _("It will not work well if " + \
		                                          "the area's edges are blurry")
		return [label_warning1, label_warning2]

	############################################################################

	def on_press_on_area(self, event, surface, event_x, event_y):
		self.set_common_values(event.button, event_x, event_y)

	def on_release_on_area(self, event, surface, event_x, event_y):
		# Guard clause: we can't paint outside of the surface
		if event_x < 0 or event_x >= surface.get_width() \
		or event_y < 0 or event_y >= surface.get_height():
			return

		if self.get_option_value('paint_algo') in ('fill', 'replace'):
			self._magic_path = utilities_get_magic_path(surface, \
			                                          event_x, event_y)
			if self._magic_path is None:
				return

		operation = self.build_operation(event_x, event_y)
		self.apply_operation(operation)

	############################################################################

	def build_operation(self, x, y):
		operation = {
			'tool_id': self.id,
			'algo': self.get_option_value('paint_algo'),
			# 'x': x,
			# 'y': y,
			'new_rgba': self.main_color,
			'antialias': self._use_antialias,
			'path': self._magic_path
		}
		return operation

	def do_tool_operation(self, operation):
		self.start_tool_operation(operation) # XXX expose antialiasing option?

		if operation['algo'] == 'replace':
			self._op_replace(operation)
		elif operation['algo'] == 'whole':
			self._op_whole(operation)
		else: # if operation['algo'] == 'fill':
			self._op_fill(operation)

	############################################################################

	def _op_whole(self, operation):
		"""Paint the entire image regardless of existing pixels"""
		cairo_context = self.get_context()
		cairo_context.set_source_rgba(*operation['new_rgba'])
		cairo_context.paint()

	def _op_fill(self, operation):
		"""Blend the new color over the connected region."""
		if operation['path'] is None:
			return
		cairo_context = self.get_context()
		cairo_context.set_source_rgba(*operation['new_rgba'])
		cairo_context.append_path(operation['path'])
		cairo_context.fill()

	def _op_replace(self, operation):
		if operation['path'] is None:
			return
		# The path already identifies the exact region, so replacing its
		# pixels directly also handles transparent colors without disturbing
		# neighboring pixels or creating a temporary copy of the image.
		context = self.get_context()
		context.append_path(operation['path'])
		context.set_operator(cairo.Operator.SOURCE)
		context.set_source_rgba(*operation['new_rgba'])
		context.fill()

	############################################################################
################################################################################
