# tool_arc.py
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
from .abstract_classic_tool import AbstractClassicTool
from .utilities_paths import utilities_add_arrow_triangle

class ToolArc(AbstractClassicTool):
	__gtype_name__ = 'ToolArc'

	def __init__(self, window, **kwargs):
		super().__init__('arc', _("Curve"), 'tool-arc-symbolic', window)

		self.add_tool_action_enum('line_shape', 'round')
		self.add_tool_action_boolean('use_dashes', False)
		self.add_tool_action_boolean('is_arrow', False)

		# Default values
		self._shape_label = _("Round")
		self._shape_id = cairo.LineCap.ROUND

		self._1st_segment = None
		self._use_dashes = False
		self._use_arrow = False

	def give_back_control(self, preserve_selection):
		self._1st_segment = None
		self.x_press = 0.0
		self.y_press = 0.0
		self.restore_pixbuf()

	############################################################################
	# Options ##################################################################

	def set_active_shape(self):
		if self.get_option_value('line_shape') == 'square':
			self._shape_id = cairo.LineCap.BUTT
			self._shape_label = _("Square")
		else:
			self._shape_id = cairo.LineCap.ROUND
			self._shape_label = _("Round")

	def get_options_label(self):
		return _("Curve options")

	def get_edition_status(self):
		self._use_dashes = self.get_option_value('use_dashes')
		self._use_arrow = self.get_option_value('is_arrow')
		self.set_active_shape()
		label = self.label
		if self._use_arrow and self._use_dashes:
			label = label + ' - ' + _("Dashed arrow")
		elif self._use_arrow:
			label = label + ' - ' + _("Arrow")
		elif self._use_dashes:
			label = label + ' - ' + _("Dashed")
		return label

	############################################################################

	def on_press_on_area(self, event, surface, event_x, event_y):
		self.set_common_values(event.button)
		self.x_press = event_x
		self.y_press = event_y

	def on_motion_on_area(self, event, surface, event_x, event_y):
		cairo_context = self.get_context()
		if self._1st_segment is None:
			cairo_context.move_to(self.x_press, self.y_press)
			cairo_context.line_to(event_x, event_y)
		else:
			cairo_context.move_to(self._1st_segment[0], self._1st_segment[1])
			cairo_context.curve_to(self._1st_segment[2], self._1st_segment[3], \
			                       self.x_press, self.y_press, event_x, event_y)
		self._path = cairo_context.copy_path()
		operation = self.build_operation(event_x, event_y, True)
		self.do_tool_operation(operation)

	def on_release_on_area(self, event, surface, event_x, event_y):
		if self._1st_segment is None:
			self._1st_segment = (self.x_press, self.y_press, event_x, event_y)
			return
		else:
			self.restore_pixbuf()
			cairo_context = self.get_context()
			cairo_context.move_to(self._1st_segment[0], self._1st_segment[1])
			cairo_context.curve_to(self._1st_segment[2], self._1st_segment[3], \
			                       self.x_press, self.y_press, event_x, event_y)
			self._1st_segment = None

		self._path = cairo_context.copy_path()
		operation = self.build_operation(event_x, event_y, False)
		self.apply_operation(operation)
		self.x_press = 0.0
		self.y_press = 0.0

	############################################################################

	def build_operation(self, event_x, event_y, is_preview):
		operation = {
			'tool_id': self.id,
			'rgba': self.main_color,
			'is_preview': is_preview,
			'operator': self.get_operator_enum(),
			'line_width': self.tool_width,
			'line_cap': self._shape_id,
			'use_dashes': self._use_dashes,
			'use_arrow': self._use_arrow,
			'path': self._path,
			'x_release': event_x,
			'y_release': event_y,
			'x_press': self.x_press,
			'y_press': self.y_press
		}
		return operation

	def do_tool_operation(self, operation):
		self.start_tool_operation(operation)
		cairo_context = self.get_context()
		cairo_context.set_line_cap(operation['line_cap'])
		line_width = operation['line_width']
		cairo_context.set_line_width(line_width)
		rgba = operation['rgba']
		cairo_context.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)
		if operation['use_dashes']:
			cairo_context.set_dash([2 * line_width, 2 * line_width])
		cairo_context.append_path(operation['path'])

		self.stroke_with_operator(operation['operator'], cairo_context, \
		                                    line_width, operation['is_preview'])

		if operation['use_arrow']:
			x1 = operation['x_press']
			y1 = operation['y_press']
			x2 = operation['x_release']
			y2 = operation['y_release']
			utilities_add_arrow_triangle(cairo_context, x2, y2, x1, y1, line_width)

	############################################################################
################################################################################

