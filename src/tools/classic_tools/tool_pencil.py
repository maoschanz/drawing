# tool_pencil.py
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

import cairo, math
from .abstract_classic_tool import AbstractClassicTool
from .utilities_paths import utilities_smooth_path

class ToolPencil(AbstractClassicTool):
	__gtype_name__ = 'ToolPencil'

	def __init__(self, window, **kwargs):
		super().__init__('pencil', _("Pencil"), 'tool-pencil-symbolic', window)
		self.use_operator = True

		self._path = None
		self._shape_label = _("Round")
		self._cap_id = cairo.LineCap.ROUND
		self._join_id = cairo.LineCap.ROUND
		self._dashes_type = 'none'
		self._use_outline = False

		self.add_tool_action_enum('line_shape', 'round')
		self.add_tool_action_enum('dashes-type', self._dashes_type)
		self.add_tool_action_boolean('pencil-outline', self._use_outline)

	def _set_active_shape(self, *args):
		state_as_string = self.get_option_value('line_shape')
		if state_as_string == 'thin':
			self._cap_id = cairo.LineCap.BUTT
			self._join_id = cairo.LineJoin.BEVEL
			self._shape_label = _("Square")
		else:
			self._cap_id = cairo.LineCap.ROUND
			self._join_id = cairo.LineJoin.ROUND
			self._shape_label = _("Round")

	def get_options_label(self):
		return _("Pencil options")

	def get_edition_status(self):
		self._dashes_type = self.get_option_value('dashes-type')
		use_dashes = self._dashes_type != 'none'
		self._use_outline = self.get_option_value('pencil-outline')
		self._set_active_shape()
		label = self.label
		if use_dashes:
			label = label + ' - ' + _("Dashed")
		return label

	############################################################################

	def on_press_on_area(self, event, surface, event_x, event_y):
		self.set_common_values(event.button, event_x, event_y)
		self._path = None

	def _add_point(self, event_x, event_y):
		cairo_context = self.get_context()
		if self._path is None:
			cairo_context.move_to(self.x_press, self.y_press)
		else:
			cairo_context.append_path(self._path)
		cairo_context.line_to(event_x, event_y)
		self._path = cairo_context.copy_path()

	def on_motion_on_area(self, event, surface, event_x, event_y, render=True):
		self._add_point(event_x, event_y)
		if render:
			operation = self.build_operation()
			self.do_tool_operation(operation)

	def on_release_on_area(self, event, surface, event_x, event_y):
		self._add_point(event_x, event_y)
		operation = self.build_operation()
		self.apply_operation(operation)

	############################################################################

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'rgba': self.main_color,
			'rgba2': self.secondary_color,
			'antialias': self._use_antialias,
			'outline': self._use_outline,
			'operator': self._operator,
			'line_width': self.tool_width,
			'line_cap': self._cap_id,
			'line_join': self._join_id,
			'dashes': self._dashes_type,
			'path': self._path
		}
		return operation

	def do_tool_operation(self, operation):
		if operation['path'] is None:
			return
		cairo_context = self.start_tool_operation(operation)

		cairo_context.set_operator(operation['operator'])
		line_width = operation['line_width']
		self.set_dashes_and_cap(cairo_context, line_width, \
		                        operation['dashes'], operation['line_cap'])
		cairo_context.set_line_join(operation['line_join']) # XXX useless?

		utilities_smooth_path(cairo_context, operation['path'])

		if operation['outline']:
			rgba = operation['rgba2']
			cairo_context.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)
			cairo_context.set_line_width(line_width * 1.2 + 2)
			cairo_context.stroke_preserve()

		rgba = operation['rgba']
		cairo_context.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)
		cairo_context.set_line_width(line_width)
		cairo_context.stroke()

	############################################################################
################################################################################

