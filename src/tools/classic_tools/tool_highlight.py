# tool_highlight.py

import cairo

from .tool_pencil import ToolPencil
from .utilities_tools import utilities_smooth_path
from .abstract_classic_tool import AbstractClassicTool

class ToolHighlighter(ToolPencil):
	__gtype_name__ = 'ToolHighlighter'

	def __init__(self, window, **kwargs):
		super().__init__(window)
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
		AbstractClassicTool.do_tool_operation(self, operation)
		if operation['path'] is None:
			return
		cairo_context = self.get_context()
		cairo_context.set_line_cap(cairo.LineCap.SQUARE)
		cairo_context.set_line_join(cairo.LineJoin.ROUND)
		line_width = operation['line_width']
		rgba = operation['rgba']
		cairo_context.set_source_rgba(rgba.red, rgba.green, rgba.blue, 0.5)
		utilities_smooth_path(cairo_context, operation['path'])
		self.stroke_with_operator(cairo.Operator.OVER, cairo_context, \
		                                                      line_width, False)

	############################################################################
################################################################################

