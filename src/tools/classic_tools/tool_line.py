# tool_line.py

import cairo
from gi.repository import Gtk, Gdk

from .abstract_classic_tool import AbstractClassicTool
from .utilities_tools import utilities_add_arrow_triangle

class ToolLine(AbstractClassicTool):
	__gtype_name__ = 'ToolLine'

	def __init__(self, window, **kwargs):
		super().__init__('line', _("Line"), 'tool-line-symbolic', window)
		self.use_size = True

		self.add_tool_action_enum('line_shape', 'round')
		self.add_tool_action_boolean('use_dashes', False)
		self.add_tool_action_boolean('is_arrow', False)
		self.add_tool_action_boolean('use_gradient', False)
		self.set_options_attributes() # Not optimal but more readable

	def set_active_shape(self):
		if self.get_option_value('line_shape') == 'square':
			self.selected_end_id = cairo.LineCap.BUTT
			self.selected_shape_label = _("Square")
		else:
			self.selected_end_id = cairo.LineCap.ROUND
			self.selected_shape_label = _("Round")

	def get_options_label(self):
		return _("Line options")

	def set_options_attributes(self):
		self.use_dashes = self.get_option_value('use_dashes')
		self.use_arrow = self.get_option_value('is_arrow')
		self.use_gradient = self.get_option_value('use_gradient')
		self.set_active_shape()

	def get_edition_status(self): # TODO l'opérateur est important
		self.set_options_attributes()
		label = self.label
		if self.use_arrow and self.use_dashes:
			label = label + ' - ' + _("Dashed arrow")
		elif self.use_arrow:
			label = label + ' - ' + _("Arrow")
		elif self.use_dashes:
			label = label + ' - ' + _("Dashed")
		return label

	def give_back_control(self, preserve_selection):
		self.x_press = 0.0
		self.y_press = 0.0

	def on_press_on_area(self, event, surface, event_x, event_y):
		self.x_press = event_x
		self.y_press = event_y
		self.set_common_values(event.button)

	def on_motion_on_area(self, event, surface, event_x, event_y):
		self.restore_pixbuf()
		cairo_context = cairo.Context(self.get_surface())
		cairo_context.move_to(self.x_press, self.y_press)
		cairo_context.line_to(event_x, event_y)

		self._path = cairo_context.copy_path()
		operation = self.build_operation(event_x, event_y, True)
		self.do_tool_operation(operation)

	def on_release_on_area(self, event, surface, event_x, event_y):
		self.restore_pixbuf()
		cairo_context = cairo.Context(self.get_surface())
		cairo_context.move_to(self.x_press, self.y_press)
		cairo_context.line_to(event_x, event_y)

		self._path = cairo_context.copy_path()
		operation = self.build_operation(event_x, event_y, False)
		self.apply_operation(operation)
		self.x_press = 0.0
		self.y_press = 0.0

	def build_operation(self, event_x, event_y, is_preview):
		operation = {
			'tool_id': self.id,
			'rgba': self.main_color,
			'rgba2': self.secondary_color,
			'operator': self.get_operator_enum(),
			'line_width': self.tool_width,
			'line_cap': self.selected_end_id,
			'use_dashes': self.use_dashes,
			'use_arrow': self.use_arrow,
			'use_gradient': self.use_gradient,
			'is_preview': is_preview,
			'path': self._path,
			'x_release': event_x,
			'y_release': event_y,
			'x_press': self.x_press,
			'y_press': self.y_press
		}
		return operation

	def do_tool_operation(self, operation):
		super().do_tool_operation(operation)
		cairo_context = cairo.Context(self.get_surface())
		cairo_context.set_operator(operation['operator'])
		cairo_context.set_line_cap(operation['line_cap'])
		line_width = operation['line_width']
		cairo_context.set_line_width(line_width)
		c1 = operation['rgba']
		c2 = operation['rgba2']
		if operation['use_gradient']:
			pattern = cairo.LinearGradient( \
			                     operation['x_press'], operation['y_press'], \
			                     operation['x_release'], operation['y_release'])
			pattern.add_color_stop_rgba(0.1, c1.red, c1.green, c1.blue, c1.alpha)
			pattern.add_color_stop_rgba(0.9, c2.red, c2.green, c2.blue, c2.alpha)
			cairo_context.set_source(pattern)
		else:
			cairo_context.set_source_rgba(c1.red, c1.green, c1.blue, c1.alpha)
		if operation['use_dashes']:
			cairo_context.set_dash([2*line_width, 2*line_width])
		cairo_context.append_path(operation['path'])

		self.stroke_with_operator(operation['operator'], cairo_context, \
		                                    line_width, operation['is_preview'])

		if operation['use_arrow']:
			x_press = operation['x_press']
			y_press = operation['y_press']
			x_release = operation['x_release']
			y_release = operation['y_release']
			utilities_add_arrow_triangle(cairo_context, x_release, y_release, \
			                                       x_press, y_press, line_width)

	############################################################################
################################################################################

