# tool_line.py
#
# Copyright 2018-2020 Romain F. T.
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
from .abstract_tool import AbstractAbstractTool
from .utilities import utilities_add_arrow_triangle

class ToolLine(AbstractAbstractTool):
	__gtype_name__ = 'ToolLine'

	def __init__(self, window, **kwargs):
		super().__init__('line', _("Line"), 'tool-line-symbolic', window)
		self.use_size = True

		self.add_tool_action_enum('line_shape', 'round')
		self.add_tool_action_boolean('use_dashes', False)
		self.add_tool_action_boolean('is_arrow', False)
		self.add_tool_action_boolean('use_gradient', False)
		self.add_tool_action_enum('cairo_operator', 'over')

		# Default values
		self._shape_label = _("Round")
		self.selected_operator = cairo.Operator.OVER
		self._cap_id = cairo.LineCap.ROUND
		self.use_dashes = False
		self.use_arrow = False

	def _set_active_shape(self):
		state_as_string = self.get_option_value('line_shape')
		if state_as_string == 'thin':
			self._cap_id = cairo.LineCap.BUTT
			self._shape_label = _("Thin")
		elif state_as_string == 'square':
			self._cap_id = cairo.LineCap.SQUARE
			self._shape_label = _("Square")

	def _set_active_operator(self):
		state_as_string = self.get_option_value('cairo_operator')
		if state_as_string == 'difference':
			self.selected_operator = cairo.Operator.DIFFERENCE
			self.selected_operator_label = _("Difference")
		elif state_as_string == 'source':
			self.selected_operator = cairo.Operator.SOURCE
			self.selected_operator_label = _("Source color")
		elif state_as_string == 'clear':
			self.selected_operator = cairo.Operator.CLEAR
			self.selected_operator_label = _("Eraser")
		else:
			self.selected_operator = cairo.Operator.OVER
			self.selected_operator_label = _("Classic")

	def get_options_label(self):
		return _("Line options")

	def get_edition_status(self):
		# TODO l'opérateur est important
		self.use_dashes = self.get_option_value('use_dashes')
		self.use_arrow = self.get_option_value('is_arrow')
		self.use_gradient = self.get_option_value('use_gradient')
		self._set_active_shape()
		self._set_active_operator()
		label = self.label + ' (' + self._shape_label + ') '
		if self.use_arrow and self.use_dashes:
			label = label + ' - ' + _("Arrow") + ' - ' + _("With dashes")
		elif self.use_arrow:
			label = label + ' - ' + _("Arrow")
		elif self.use_dashes:
			label = label + ' - ' + _("With dashes")
		return label

	def give_back_control(self, preserve_selection):
		self.x_press = 0.0
		self.y_press = 0.0

	############################################################################

	def on_press_on_area(self, event, surface, tool_width, left_color, right_color, event_x, event_y):
		self.x_press = event_x
		self.y_press = event_y
		self.tool_width = tool_width
		if event.button == 1:
			self.main_color = left_color
			self.sec_color = right_color
		elif event.button == 3:
			self.main_color = right_color
			self.sec_color = left_color

	def on_motion_on_area(self, event, surface, event_x, event_y):
		operation = self.build_operation(event_x, event_y)
		self.do_tool_operation(operation)

	def on_release_on_area(self, event, surface, event_x, event_y):
		operation = self.build_operation(event_x, event_y)
		self.apply_operation(operation)

	############################################################################

	def build_operation(self, event_x, event_y):
		operation = {
			'tool_id': self.id,
			'rgba': self.main_color,
			'rgba2': self.sec_color,
			'operator': self.selected_operator,
			'line_width': self.tool_width,
			'line_cap': self._cap_id,
			'use_dashes': self.use_dashes,
			'use_arrow': self.use_arrow,
			'use_gradient': self.use_gradient,
			'x_release': event_x,
			'y_release': event_y,
			'x_press': self.x_press,
			'y_press': self.y_press
		}
		return operation

	def do_tool_operation(self, operation):
		if operation['tool_id'] != self.id:
			return
		self.restore_pixbuf()
		cairo_context = cairo.Context(self.get_surface())
		cairo_context.set_operator(operation['operator'])
		cairo_context.set_line_cap(operation['line_cap'])
		line_width = operation['line_width']
		cairo_context.set_line_width(line_width)
		c1 = operation['rgba']
		c2 = operation['rgba2']
		x1 = operation['x_press']
		y1 = operation['y_press']
		x2 = operation['x_release']
		y2 = operation['y_release']
		if operation['use_gradient']:
			pattern = cairo.LinearGradient(x1, y1, x2, y2)
			pattern.add_color_stop_rgba(0.1, c1.red, c1.green, c1.blue, c1.alpha)
			pattern.add_color_stop_rgba(0.9, c2.red, c2.green, c2.blue, c2.alpha)
			cairo_context.set_source(pattern)
		else:
			cairo_context.set_source_rgba(c1.red, c1.green, c1.blue, c1.alpha)
		if operation['use_dashes']:
			cairo_context.set_dash([2 * line_width, 2 * line_width])
		cairo_context.move_to(x1, y1)
		cairo_context.line_to(x2, y2)
		cairo_context.stroke()

		if operation['use_arrow']:
			utilities_add_arrow_triangle(cairo_context, x2, y2, x1, y1, line_width)

	############################################################################
################################################################################

