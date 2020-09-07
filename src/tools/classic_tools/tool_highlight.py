# tool_highlight.py
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
from .tool_pencil import ToolPencil
from .utilities_paths import utilities_smooth_path
from .abstract_classic_tool import AbstractClassicTool

class ToolHighlighter(ToolPencil):
	__gtype_name__ = 'ToolHighlighter'

	def __init__(self, window, **kwargs):
		super().__init__(window)
		# Context: this is the name of a tool, a thick pencil dedicated to
		# highlight text, for example in screenshots
		AbstractClassicTool.__init__(self, 'highlight', _("Highlighter"), \
		                                      'tool-highlight-symbolic', window)

	def get_options_model(self):
		return None

	def get_options_label(self):
		return _("No options")

	############################################################################

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'rgba': self.main_color,
			'line_width': self.tool_width,
			'path': self._path
		}
		return operation

	def do_tool_operation(self, operation):
		self.start_tool_operation(operation)
		if operation['path'] is None:
			return
		cairo_context = self.get_context()
		cairo_context.set_line_cap(cairo.LineCap.SQUARE)
		cairo_context.set_line_join(cairo.LineJoin.ROUND)
		line_width = operation['line_width']
		rgba = operation['rgba']
		cairo_context.set_source_rgba(rgba.red, rgba.green, rgba.blue, 0.5)
		utilities_smooth_path(cairo_context, operation['path'])
		self.stroke_with_operator(cairo.Operator.MULTIPLY, cairo_context, \
		                                                      line_width, False)

	############################################################################
################################################################################

