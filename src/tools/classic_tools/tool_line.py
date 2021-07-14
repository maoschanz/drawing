# tool_line.py
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
from .abstract_classic_tool import AbstractClassicTool
from .utilities_paths import utilities_add_arrow_triangle

class ToolLine(AbstractClassicTool):
	__gtype_name__ = 'ToolLine'

	def __init__(self, window, **kwargs):
		super().__init__('line', _("Line"), 'tool-line-symbolic', window)
		self.use_operator = True

		self._use_outline = False
		self._dashes_type = 'none'
		self._arrow_type = 'none'
		self._use_gradient = False
		# Lock the tool to only draw orthogonal lines (multiples of 45°)
		self._ortholock = False # Unrelated to Maïté's ortolan.

		self.add_tool_action_enum('line_shape', 'round')
		self.add_tool_action_enum('dashes-type', self._dashes_type)
		self.add_tool_action_enum('arrow-type', self._arrow_type)
		self.add_tool_action_boolean('use_gradient', self._use_gradient)
		self.add_tool_action_boolean('pencil-outline', self._use_outline)
		self.add_tool_action_boolean('line-ortholock', self._ortholock)
		self._set_options_attributes() # Not optimal but more readable

	def _set_active_shape(self):
		state_as_string = self.get_option_value('line_shape')
		if state_as_string == 'thin':
			self._cap_id = cairo.LineCap.BUTT
		else:
			self._cap_id = cairo.LineCap.ROUND

	def get_options_label(self):
		return _("Line options")

	def _set_options_attributes(self):
		self._use_outline = self.get_option_value('pencil-outline')
		self._dashes_type = self.get_option_value('dashes-type')
		self._arrow_type = self.get_option_value('arrow-type')
		self._use_gradient = self.get_option_value('use_gradient')
		self._ortholock = self.get_option_value('line-ortholock')
		self._set_active_shape()

	def get_edition_status(self):
		self._set_options_attributes()
		is_arrow = self._arrow_type != 'none'
		use_dashes = self._dashes_type != 'none'
		label = self.label
		if is_arrow and use_dashes:
			label = label + ' - ' + _("Dashed arrow")
		elif is_arrow:
			label = label + ' - ' + _("Arrow")
		elif use_dashes:
			label = label + ' - ' + _("Dashed")
		return label

	############################################################################

	def on_press_on_area(self, event, surface, event_x, event_y):
		self.set_common_values(event.button, event_x, event_y)

	def on_motion_on_area(self, event, surface, event_x, event_y, render=True):
		if render:
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
			'rgba2': self.secondary_color,
			'antialias': self._use_antialias,
			'operator': self._operator,
			'line_width': self.tool_width,
			'line_cap': self._cap_id,
			'dashes': self._dashes_type,
			'arrow': self._arrow_type,
			'gradient': self._use_gradient,
			'outline': self._use_outline,
			'ortholock': self._ortholock,
			'x_release': event_x,
			'y_release': event_y,
			'x_press': self.x_press,
			'y_press': self.y_press
		}
		return operation

	def do_tool_operation(self, operation):
		cairo_context = self.start_tool_operation(operation)
		cairo_context.set_operator(operation['operator'])
		line_width = operation['line_width']
		cairo_context.set_line_width(line_width)
		c1 = operation['rgba']
		c2 = operation['rgba2']
		x1 = operation['x_press']
		y1 = operation['y_press']
		x2 = operation['x_release']
		y2 = operation['y_release']

		if operation['ortholock']:
			x1, y1 = int(x1), int(y1)
			x2, y2 = int(x2), int(y2)
			delta_x = abs(x1 - x2)
			delta_y = abs(y1 - y2)
			if delta_x > 2 * delta_y:
				# Strictly horizontal line
				y2 = y1
			elif delta_x * 2 < delta_y:
				# Strictly vertical line
				x2 = x1
			else:
				# 45° line
				delta45 = min(delta_x, delta_y)
				x2 = x1 + delta45 if (x1 - x2 < 0) else x1 - delta45
				y2 = y1 + delta45 if (y1 - y2 < 0) else y1 - delta45

		self.set_dashes_and_cap(cairo_context, line_width, \
		                             operation['dashes'], operation['line_cap'])

		if operation['arrow'] == 'double':
			utilities_add_arrow_triangle(cairo_context, x1, y1, x2, y2, line_width)

		# We don't memorize the path because all coords are here anyway for the
		# linear gradient and/or the arrow.
		cairo_context.move_to(x1, y1)
		cairo_context.line_to(x2, y2)

		if operation['arrow'] != 'none':
			utilities_add_arrow_triangle(cairo_context, x2, y2, x1, y1, line_width)

		if operation['outline']:
			cairo_context.set_source_rgba(c2.red, c2.green, c2.blue, c2.alpha)
			cairo_context.set_line_width(line_width * 1.2 + 2)
			cairo_context.stroke_preserve()

		if operation['gradient']:
			pattern = cairo.LinearGradient(x1, y1, x2, y2)
			pattern.add_color_stop_rgba(0.1, c1.red, c1.green, c1.blue, c1.alpha)
			pattern.add_color_stop_rgba(0.9, c2.red, c2.green, c2.blue, c2.alpha)
			cairo_context.set_source(pattern)
		else:
			cairo_context.set_source_rgba(c1.red, c1.green, c1.blue, c1.alpha)
		cairo_context.set_line_width(line_width)
		cairo_context.stroke()

	############################################################################
################################################################################

