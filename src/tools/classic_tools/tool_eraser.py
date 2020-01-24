# tool_eraser.py

import cairo

from .tool_pencil import ToolPencil
from .utilities_tools import utilities_smooth_path
from .abstract_classic_tool import AbstractClassicTool

class ToolEraser(ToolPencil):
	__gtype_name__ = 'ToolEraser'

	def __init__(self, window, **kwargs):
		super().__init__(window)
		AbstractClassicTool.__init__(self, 'eraser', _("Eraser"), \
		                                         'tool-eraser-symbolic', window)
		self.use_color = False

	def get_options_model(self):
		return None

	def get_options_label(self):
		return _("No options")

	############################################################################

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'line_width': self.tool_width,
			'line_cap': self.selected_cap_id,
			'line_join': self.selected_join_id,
			'path': self._path
		}
		return operation

	def do_tool_operation(self, operation):
		AbstractClassicTool.do_tool_operation(self, operation)

		if operation['path'] is None:
			return
		cairo_context = self.get_context()
		cairo_context.set_line_cap(cairo.LineCap.ROUND)
		cairo_context.set_line_join(cairo.LineJoin.ROUND)
		line_width = operation['line_width']
		utilities_smooth_path(cairo_context, operation['path'])
		self.stroke_with_operator(cairo.Operator.CLEAR, cairo_context, \
		                                                      line_width, False)

	############################################################################
################################################################################

