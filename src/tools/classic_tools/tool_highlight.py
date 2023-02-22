# tool_highlight.py
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
from .tool_pencil import ToolPencil
from .abstract_classic_tool import AbstractClassicTool

class ToolHighlighter(ToolPencil):
	__gtype_name__ = 'ToolHighlighter'

	def __init__(self, window, **kwargs):
		# Context: this is the name of a tool, a thick pencil dedicated to
		# highlight text, for example in screenshots
		AbstractClassicTool.__init__(self, 'highlight', _("Highlighter"), \
		                                      'tool-highlight-symbolic', window)
		self.use_operator = True
		self._path = None
		self.add_tool_action_boolean('highlight-alpha', True)
		self.add_tool_action_boolean('highlight-rigid', True)
		self.add_tool_action_enum('highlight-bg', 'light')

	def get_editing_tips(self):
		self._bg_type = self.get_option_value('highlight-bg')
		self._force_alpha = self.get_option_value('highlight-alpha')
		self._is_rigid = self.get_option_value('highlight-rigid')

		label_options = self.label + " - "
		if self._bg_type == 'light':
			label_options += _("Dark text on light background")
			label_modifier_shift = _("Press <Shift> to temporarily highlight" + \
			                                      " on dark background instead")
		else:
			label_options += _("Light text on dark background")
			label_modifier_shift = _("Press <Shift> to temporarily highlight" + \
			                                     " on light background instead")
		if self.get_image().get_mouse_is_pressed():
			label_modifier_shift = None

		full_list = [label_options, label_modifier_shift]
		return list(filter(None, full_list))

	def get_options_label(self):
		return _("Highlighter options")

	############################################################################

	def on_press_on_area(self, event, surface, event_x, event_y):
		self.set_common_values(event.button, event_x, event_y)
		self._path = None

		self.update_modifier_state(event.state)
		if 'SHIFT' in self._modifier_keys:
			if self._bg_type == 'light':
				self._bg_type = 'dark'
			else:
				self._bg_type = 'light'

	def _add_point(self, event_x, event_y):
		cairo_context = self.get_context()
		if self._path is None:
			cairo_context.move_to(self.x_press, self.y_press)
		elif self._didnt_really_move(cairo_context, event_x, event_y):
			length = -1
			for pts in self._path:
				if pts[1] == ():
					continue
				length += 1
				# a better technique to find the length probably exists
			for index, pts in enumerate(self._path):
				if pts[1] == ():
					continue
				if pts[0] == cairo.PathDataType.MOVE_TO:
					cairo_context.move_to(pts[1][0], pts[1][1])
				elif index == length:
					event_x = (pts[1][0] + event_x) / 2
					event_y = (pts[1][1] + event_y) / 2
					break
				else: # if pts[0] == cairo.PathDataType.LINE_TO:
					cairo_context.line_to(pts[1][0], pts[1][1])
		cairo_context.line_to(event_x, event_y)
		self._path = cairo_context.copy_path()

	def _didnt_really_move(self, cairo_context, event_x, event_y):
		"""Tells if the pointer has moved enough to add a new point, otherwise
		the last point will be changed.
		It's an option that can be disabled.
		The context of an highlighter tool means the direction is biased: i will
		assume the underlying text is written horizontally, and in straight
		lines; so the highlighting will also be straight, but the chosen line
		may change during the stroke."""
		cairo_context.append_path(self._path)
		if not self._is_rigid:
			return False

		rigidity = min(self.tool_width, 10.0)
		if abs(cairo_context.get_current_point()[0] - event_x) > rigidity:
			return False
		if abs(cairo_context.get_current_point()[1] - event_y) > rigidity / 5:
			return False

		cairo_context.new_path()
		return True

	def on_motion_on_area(self, event, surface, event_x, event_y, render=True):
		self._add_point(event_x, event_y)
		if not render:
			return
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
			'width': self.tool_width,
			'path': self._path,
			'bg-type': self._bg_type,
			'halpha': self._force_alpha
		}
		return operation

	def do_tool_operation(self, operation):
		self.start_tool_operation(operation)
		if operation['path'] is None:
			return
		ccontext = self.get_context()
		ccontext.set_line_cap(cairo.LineCap.SQUARE)
		ccontext.set_line_join(cairo.LineJoin.ROUND)
		ccontext.set_line_width(operation['width'])

		if operation['bg-type'] == 'light':
			operator = cairo.Operator.MULTIPLY
		else:
			operator = cairo.Operator.SCREEN
		ccontext.set_operator(operator)

		main_color = operation['rgba']
		if operation['halpha']:
			main_color[3] = 0.5
		ccontext.set_source_rgba(*main_color)

		ccontext.append_path(operation['path'])
		ccontext.stroke()

	############################################################################
################################################################################

