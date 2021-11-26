# Licensed under GPL3 https://github.com/maoschanz/drawing/blob/master/LICENSE

from .tool_arc import ToolArc
from .tool_brush import ToolBrush
from .tool_eraser import ToolEraser
from .tool_experiment import ToolExperiment
from .tool_highlight import ToolHighlighter
from .tool_line import ToolLine
from .tool_paint import ToolPaint
from .tool_pencil import ToolPencil
from .tool_picker import ToolPicker
from .tool_points import ToolPoints
from .tool_shape import ToolShape
from .tool_text import ToolText

from .select_rect import ToolRectSelect
from .select_free import ToolFreeSelect
from .select_color import ToolColorSelect

from .tool_crop import ToolCrop
from .tool_filters import ToolFilters
from .tool_rotate import ToolRotate
from .tool_scale import ToolScale
from .tool_skew import ToolSkew

################################################################################

class DrToolsInitializer():

	def __init__(self, window):
		self._window = window
		self._tools = {}

	def load_all_tools(self, dev, disabled_tools):

		# The order might be improvable
		self._load_tool('pencil', ToolPencil, disabled_tools, dev)
		self._load_tool('brush', ToolBrush, disabled_tools, dev)
		self._load_tool('eraser', ToolEraser, disabled_tools, dev)
		self._load_tool('highlight', ToolHighlighter, disabled_tools, dev)
		self._load_tool('text', ToolText, disabled_tools, dev)
		self._load_tool('points', ToolPoints, disabled_tools, dev)
		self._load_tool('rect_select', ToolRectSelect, disabled_tools, dev)
		self._load_tool('free_select', ToolFreeSelect, disabled_tools, dev)
		self._load_tool('line', ToolLine, disabled_tools, dev)
		self._load_tool('arc', ToolArc, disabled_tools, dev)
		self._load_tool('shape', ToolShape, disabled_tools, dev)
		self._load_tool('picker', ToolPicker, disabled_tools, dev)
		self._load_tool('color_select', ToolColorSelect, disabled_tools, dev)
		self._load_tool('paint', ToolPaint, disabled_tools, dev)
		if dev:
			self._load_tool('experiment', ToolExperiment, disabled_tools, dev)
		self._load_tool('crop', ToolCrop, disabled_tools, dev)
		self._load_tool('scale', ToolScale, disabled_tools, dev)
		self._load_tool('rotate', ToolRotate, disabled_tools, dev)
		self._load_tool('skew', ToolSkew, disabled_tools, dev)
		self._load_tool('filters', ToolFilters, disabled_tools, dev)

		self._add_auto_mnemonics()
		return self._tools

	############################################################################

	def _load_tool(self, tool_id, tool_class, disabled_tools, dev):
		"""Given its id and its python class, this method tries to load a tool,
		and show an error message if the tool initialization failed."""
		if tool_id not in disabled_tools:
			try:
				self._tools[tool_id] = tool_class(self._window)
			except Exception as err:
				# Context: an error message
				self._window.reveal_action_report(_("Failed to load tool: %s") % tool_id)
				traceback.print_exc()

	def _add_auto_mnemonics(self):
		# I don't want useful tools lacking a mnemonic accelerator because a
		# useless one "stole" its letters, so the mnemonics are decided in the
		# following order:
		sorted_tools = [
			'pencil',
			'text',
			'rect_select',
			'crop',
			'scale',
			'rotate',
			'shape',
			'filters',
			'line',
			'highlight',
			'arc',
			'picker',
			'brush',
			'free_select',
			'eraser',
			'skew',
			'paint',
			'color_select',
			'points',
			'experiment'
		]
		for tool_id in self._tools:
			if tool_id not in sorted_tools:
				print("Warning: " + tool_id + "will not have a mnemonic")

		underlined_chars = {}
		for tool_id in sorted_tools:
			if tool_id not in self._tools:
				continue
			letter_index = 0
			while(letter_index >= 0):
				if letter_index == len(self._tools[tool_id].label):
					letter_index = -1
					continue
				ith_char = self._tools[tool_id].label[letter_index]
				letter_index += 1

				if ith_char.isalpha() \
				and ith_char.upper() not in underlined_chars.values() \
				and ith_char.lower() not in underlined_chars.values():
					underlined_chars[tool_id] = ith_char
					letter_index = -1

		for tool_id in underlined_chars:
			self._tools[tool_id].set_mnemonics(underlined_chars[tool_id])

	############################################################################
################################################################################

