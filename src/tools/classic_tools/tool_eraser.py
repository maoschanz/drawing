# tool_eraser.py
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
from .tool_pencil import ToolPencil
from .abstract_classic_tool import AbstractClassicTool
from .utilities_paths import utilities_smooth_path

class ToolEraser(ToolPencil):
	__gtype_name__ = 'ToolEraser'

	def __init__(self, window, **kwargs):
		super().__init__(window)
		# Context: this is the name of a tool, in the meaning "a rubber eraser"
		AbstractClassicTool.__init__(self, 'eraser', _("Eraser"), \
		                                         'tool-eraser-symbolic', window)
		self.use_operator = False
		self._fallback_operator = 'clear'
		self.add_tool_action_enum('selection-color', 'alpha')
		self.add_tool_action_enum('eraser-type', 'solid')

	def get_edition_status(self):
		self._eraser_type = self.get_option_value('eraser-type')
		self._replacement_type = self.get_option_value('selection-color')

		if self._eraser_type == 'solid' and self._replacement_type != 'alpha':
			self._fallback_operator = 'source'
		else:
			self._fallback_operator = 'clear'
		self.window.options_manager.update_pane(self)

		return self.label

	def get_options_label(self):
		return _("Eraser options")

	############################################################################

	def build_operation(self):
		if self._replacement_type == 'alpha':
			color = None
		elif self._replacement_type == 'initial':
			gdk_rgba = self.get_image().get_initial_rgba()
			color = [gdk_rgba.red, gdk_rgba.green, gdk_rgba.blue, gdk_rgba.alpha]
		elif self._replacement_type == 'secondary':
			gdk_rgba = self.window.options_manager.get_right_color()
			color = [gdk_rgba.red, gdk_rgba.green, gdk_rgba.blue, gdk_rgba.alpha]

		operation = {
			'tool_id': self.id,
			'line_width': self.tool_width,
			'line_cap': self._cap_id,
			'line_join': self._join_id,
			'replacement': color,
			'antialias': self._use_antialias,
			'path': self._path
		}
		return operation

	def do_tool_operation(self, operation):
		if operation['path'] is None:
			return
		cairo_context = self.start_tool_operation(operation)
		cairo_context.set_line_cap(cairo.LineCap.ROUND)
		cairo_context.set_line_join(cairo.LineJoin.ROUND)
		cairo_context.set_line_width(operation['line_width'])

		if operation['replacement'] is None:
			cairo_context.set_operator(cairo.Operator.CLEAR)
		else:
			cairo_context.set_source_rgba(*operation['replacement'])
			cairo_context.set_operator(cairo.Operator.SOURCE)

		utilities_smooth_path(cairo_context, operation['path'])
		cairo_context.stroke()

	############################################################################
################################################################################

