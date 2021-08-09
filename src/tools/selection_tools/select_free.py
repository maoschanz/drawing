# select_free.py
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
from .abstract_select import AbstractSelectionTool

class ToolFreeSelect(AbstractSelectionTool):
	__gtype_name__ = 'ToolFreeSelect'

	def __init__(self, window, **kwargs):
		# Context: this is a tool to select an area according to a shape that
		# can be freely defined by the user.
		super().__init__('free_select', _("Free selection"), 'tool-select-free-symbolic', window)
		self.closing_precision = 10
		self.closing_x = 0.0
		self.closing_y = 0.0
		self.add_tool_action_simple('selection_close', self._force_close_shape)
		self.set_action_sensitivity('selection_close', False)

	def on_tool_selected(self, *args):
		super().on_tool_selected()

	def on_tool_unselected(self, *args):
		super().on_tool_unselected()
		self.set_action_sensitivity('selection_close', False)

	############################################################################

	def press_define(self, event_x, event_y):
		self._draw_shape(event_x, event_y)
		self.set_action_sensitivity('selection_close', True)

	def motion_define(self, event_x, event_y, render):
		self._draw_shape(event_x, event_y, render)

	def release_define(self, surface, event_x, event_y):
		if self._draw_shape(event_x, event_y):
			self.restore_pixbuf()
			self.operation_type = 'op-define'
			operation = self.build_operation()
			self.apply_operation(operation)
			self.set_action_sensitivity('selection_close', False)
		else:
			return # without updating the surface so the path is visible

	############################################################################

	def _force_close_shape(self, *args):
		self.release_define(None, self.closing_x, self.closing_y)

	def _draw_shape(self, event_x, event_y, render=True):
		"""This method is specific to the 'free selection' mode. It returns a
		boolean, true if the shape should be closed."""
		cairo_context = self.get_context()
		cairo_context.set_source_rgba(0.5, 0.5, 0.5, 0.5)
		thickness = self.get_overlay_thickness()
		cairo_context.set_dash([3 * thickness, 3 * thickness])
		cairo_context.set_line_width(thickness)
		if self.get_selection().get_future_path() is None:
			self.closing_x = event_x
			self.closing_y = event_y
			cairo_context.move_to(event_x, event_y)
			self._pre_load_path(cairo_context.copy_path())
			return False
		delta_x = max(event_x, self.closing_x) - min(event_x, self.closing_x)
		delta_y = max(event_y, self.closing_y) - min(event_y, self.closing_y)
		cairo_context.append_path(self.get_selection().get_future_path())
		if (delta_x < self.closing_precision) and (delta_y < self.closing_precision):
			cairo_context.close_path()
			cairo_context.stroke_preserve()
			self._pre_load_path(cairo_context.copy_path())
			return True
		else:
			cairo_context.line_to(int(event_x), int(event_y))
			cairo_context.stroke_preserve() # draw the line without closing the path
			self._pre_load_path(cairo_context.copy_path())
			if render:
				self.non_destructive_show_modif()
			return False

	############################################################################
################################################################################

