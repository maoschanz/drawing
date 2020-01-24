# tool_pencil.py

import cairo, math

from .abstract_classic_tool import AbstractClassicTool
from .utilities_tools import utilities_smooth_path

class ToolPencil(AbstractClassicTool):
	__gtype_name__ = 'ToolPencil'

	def __init__(self, window, **kwargs):
		super().__init__('pencil', _("Pencil"), 'tool-pencil-symbolic', window)
		self._path = None

		self.selected_shape_label = _("Round")
		self.selected_cap_id = cairo.LineCap.ROUND
		self.selected_join_id = cairo.LineCap.ROUND
		self.use_dashes = False

		self.add_tool_action_enum('pencil_shape', 'round')
		self.add_tool_action_boolean('use_dashes', self.use_dashes)

	def set_active_shape(self, *args):
		state_as_string = self.get_option_value('pencil_shape')
		if state_as_string == 'thin':
			self.selected_cap_id = cairo.LineCap.BUTT
			self.selected_join_id = cairo.LineJoin.BEVEL
			self.selected_shape_label = _("Thin")
		elif state_as_string == 'square':
			self.selected_cap_id = cairo.LineCap.SQUARE
			self.selected_join_id = cairo.LineJoin.MITER
			self.selected_shape_label = _("Square")
		else:
			self.selected_cap_id = cairo.LineCap.ROUND
			self.selected_join_id = cairo.LineJoin.ROUND
			self.selected_shape_label = _("Round")

	def get_options_label(self):
		return _("Pencil options")

	def set_options_attributes(self):
		self.use_dashes = self.get_option_value('use_dashes')
		self.set_active_shape()

	def get_edition_status(self):
		self.set_options_attributes()
		label = self.label # ajouter l'opérateur cairo
		if self.use_dashes:
			label = label + ' - ' + _("Dashed")
		return label

	def on_press_on_area(self, event, surface, event_x, event_y):
		self.x_press = event_x
		self.y_press = event_y
		self.set_common_values(event.button)
		self._path = None

	def on_motion_on_area(self, event, surface, event_x, event_y):
		cairo_context = self.get_context()
		if self._path is None:
			cairo_context.move_to(self.x_press, self.y_press)
		else:
			cairo_context.append_path(self._path)
		cairo_context.line_to(event_x, event_y)
		self._path = cairo_context.copy_path()
		operation = self.build_operation()
		self.do_tool_operation(operation)

	def on_release_on_area(self, event, surface, event_x, event_y):
		operation = self.build_operation()
		operation['is_preview'] = False
		self.apply_operation(operation)

	############################################################################

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'rgba': self.main_color,
			'operator': self.get_operator_enum(),
			'line_width': self.tool_width,
			'line_cap': self.selected_cap_id,
			'line_join': self.selected_join_id,
			'use_dashes': self.use_dashes,
			'is_preview': True,
			'path': self._path
		}
		return operation

	def do_tool_operation(self, operation):
		super().do_tool_operation(operation)
		if operation['path'] is None:
			return
		cairo_context = self.get_context()
		cairo_context.set_line_cap(operation['line_cap'])
		cairo_context.set_line_join(operation['line_join'])
		line_width = operation['line_width']
		rgba = operation['rgba']
		cairo_context.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)
		if operation['use_dashes']:
			cairo_context.set_dash([2*line_width, 2*line_width])
		utilities_smooth_path(cairo_context, operation['path'])
		self.stroke_with_operator(operation['operator'], cairo_context, \
		                                    line_width, operation['is_preview'])

	############################################################################
################################################################################

