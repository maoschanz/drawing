# tool_points.py
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

import cairo, math
from .abstract_classic_tool import AbstractClassicTool

class ToolPoints(AbstractClassicTool):
	__gtype_name__ = 'ToolPoints'

	def __init__(self, window, **kwargs):
		# Context: this is the name of a tool to draw little circles, crosses,
		# or squares at precise points of the image, for example to draw a vague
		# graph, or to highlight something in an image.
		# A number can be added on the cross/circle/square to help captioning
		# the elements of an image.
		super().__init__('points', _("Points"), 'tool-points-symbolic', window)

		self.add_tool_action_enum('points_type', 'cross')
		self.add_tool_action_boolean('points_number', False)
		self.add_tool_action_simple('points_reset_num', self._reset_number)
		self.add_tool_action_simple('points_inc_num', self._increment_number)
		self.add_tool_action_simple('points_dec_num', self._decrement_number)

		self._next_number = 1
		self.on_options_changed() # Not optimal but more readable XXX useful?

	def _reset_number(self, *args):
		self._next_number = 1
		self.window.set_window_subtitles()

	def _increment_number(self, *args):
		self._next_number += 1
		self.window.set_window_subtitles()

	def _decrement_number(self, *args):
		self._next_number -= 1
		self.window.set_window_subtitles()

	def get_options_label(self):
		return _("Points options")

	def get_editing_tips(self):
		label = self.label + " - " + self._shape_label
		if self._use_number:
			label += " - " + _("Next number: %s") % self._next_number
		# A single label is returned so the next number is always visible
		return [label]

	def on_options_changed(self):
		super().on_options_changed()

		state_as_string = self.get_option_value('points_type')
		if state_as_string == 'cross':
			self._shape_label = _("Cross")
		elif state_as_string == 'x-cross':
			self._shape_label = _("X-shaped cross")
		elif state_as_string == 'square':
			self._shape_label = _("Square")
		else:
			self._shape_label = _("Circle")
		self._points_type = state_as_string

		self._use_number = self.get_option_value('points_number')
		self.set_action_sensitivity('points_reset_num', self._use_number)
		self.set_action_sensitivity('points_inc_num', self._use_number)
		self.set_action_sensitivity('points_dec_num', self._use_number)

		# refreshing the rendered operation isn't pertinent

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
		if self._use_number:
			self._increment_number()

	############################################################################

	def build_operation(self, event_x, event_y):
		if self._use_number:
			number = self._next_number
		else:
			number = None
		operation = {
			'tool_id': self.id,
			'rgba': self.main_color,
			'rgba2': self.secondary_color, # for the font of the number
			'antialias': self._use_antialias,
			'line_width': self.tool_width,
			'point_type': self._points_type,
			'number': number,
			'x': event_x,
			'y': event_y,
		}
		return operation

	def do_tool_operation(self, operation):
		cairo_context = self.start_tool_operation(operation)
		cairo_context.set_line_cap(cairo.LineCap.BUTT)
		cairo_context.set_source_rgba(*operation['rgba'])

		point_width = operation['line_width']
		line_width = max(1, int(point_width / 4))
		half_width = max(1, int(point_width / 2))
		cairo_context.set_line_width(line_width)

		x = operation['x']
		y = operation['y']

		point_type = operation['point_type']
		if point_type == 'circle':
			cairo_context.arc(x, y, half_width, 0.0, 2 * math.pi)
			cairo_context.fill()
		elif point_type == 'cross':
			# Looks awful with small sizes, either with or without antialiasing
			cairo_context.move_to(x, y - half_width)
			cairo_context.line_to(x, y + half_width)
			cairo_context.move_to(x - half_width, y)
			cairo_context.line_to(x + half_width, y)
		elif point_type == 'x-cross':
			cairo_context.move_to(x - half_width, y - half_width)
			cairo_context.line_to(x + half_width, y + half_width)
			cairo_context.move_to(x + half_width, y - half_width)
			cairo_context.line_to(x - half_width, y + half_width)
		else: # if point_type == 'square':
			cairo_context.set_line_width(point_width)
			cairo_context.move_to(x, y - half_width)
			cairo_context.line_to(x, y + half_width)

		cairo_context.stroke() # without operator support, because it wouldn't
		# make much sense, and the abstract method for them doesn't support
		# changing the line width depending on the point type (like here).

		number = operation['number']
		if number is None:
			return

		# Text size
		cairo_context.set_font_size(max(1, int(point_width * 0.8)))

		# Coordinates
		if number < 10:
			num_x = x - line_width
		elif number < 100:
			num_x = x - line_width * 2
		else:
			num_x = x - line_width * 3
		# XXX could be better with cairo.ScaledFont.text_extents()
		num_y = y + line_width

		# Outline
		for dx in [-1, 1]:
			for dy in [-1, 1]:
				cairo_context.move_to(num_x + dx, num_y + dy)
				cairo_context.show_text(str(number))
		# XXX all my text insertions could use a "layer" like the brushes

		# Text color
		cairo_context.set_source_rgba(*operation['rgba2'])

		# Cairo's "toy" text API (enough for numbers)
		cairo_context.move_to(num_x, num_y)
		cairo_context.show_text(str(number))

	############################################################################
################################################################################

