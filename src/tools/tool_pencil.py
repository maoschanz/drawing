# tool_pencil.py

from gi.repository import Gtk, Gdk
import cairo

from .abstract_tool import ToolTemplate

class ToolPencil(ToolTemplate):
	__gtype_name__ = 'ToolPencil'

	implements_panel = False

	def __init__(self, window, **kwargs):
		super().__init__('pencil', _("Pencil"), 'tool-pencil-symbolic', window, False)
		self.past_x = -1.0
		self.past_y = -1.0
		self._path = None
		self.main_color = None
		self.use_size = True

		self.selected_shape_label = _("Round")
		self.selected_cap_id = cairo.LineCap.ROUND
		self.selected_join_id = cairo.LineCap.ROUND
		self.selected_operator = cairo.Operator.OVER
		self.use_dashes = False

		self.add_tool_action_enum('pencil_shape', 'round')
		self.add_tool_action_enum('cairo_operator', 'over')
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

	def set_active_operator(self, *args):
		state_as_string = self.get_option_value('cairo_operator')
		if state_as_string == 'difference':
			self.selected_operator = cairo.Operator.DIFFERENCE
			self.selected_operator_label = _("Difference")
		elif state_as_string == 'source':
			self.selected_operator = cairo.Operator.SOURCE
			self.selected_operator_label = _("Source color")
		elif state_as_string == 'clear':
			self.selected_operator = cairo.Operator.CLEAR
			self.selected_operator_label = _("Eraser")
		else:
			self.selected_operator = cairo.Operator.OVER
			self.selected_operator_label = _("Classic")

	def get_options_label(self):
		return _("Pencil options")

	def get_edition_status(self):
		self.use_dashes = self.get_option_value('use_dashes')
		self.set_active_shape()
		self.set_active_operator()
		label = self.label + ' - ' + self.selected_shape_label
		if self.use_dashes:
			label = label + ' - ' + _("With dashes")
		return label

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color, event_x, event_y):
		self.x_press = event_x
		self.y_press = event_y
		self.tool_width = tool_width
		if event.button == 3:
			self.main_color = right_color
		else:
			self.main_color = left_color
		self._path = None

	def on_motion_on_area(self, area, event, surface, event_x, event_y):
		cairo_context = cairo.Context(self.get_surface())
		if self.past_x == -1.0:
			(self.past_x, self.past_y) = (self.x_press, self.y_press)
			cairo_context.move_to(self.x_press, self.y_press)
			self._path = cairo_context.copy_path()
		else:
			cairo_context.append_path(self._path)
		cairo_context.line_to(event_x, event_y)
		self._path = cairo_context.copy_path()
		self.past_x = event_x
		self.past_y = event_y

		operation = self.build_operation()
		self.do_tool_operation(operation)

	def on_release_on_area(self, area, event, surface, event_x, event_y):
		self.past_x = -1.0
		self.past_y = -1.0
		operation = self.build_operation()
		self.apply_operation(operation)

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'rgba': self.main_color,
			'operator': self.selected_operator,
			'line_width': self.tool_width,
			'line_cap': self.selected_cap_id,
			'line_join': self.selected_join_id,
			'use_dashes': self.use_dashes,
			'path': self._path
		}
		return operation

	def do_tool_operation(self, operation):
		if operation['tool_id'] != self.id:
			return
		if operation['path'] is None:
			return
		self.restore_pixbuf()
		cairo_context = cairo.Context(self.get_surface())
		cairo_context.set_operator(operation['operator'])
		cairo_context.set_line_cap(operation['line_cap'])
		cairo_context.set_line_join(operation['line_join'])
		line_width = operation['line_width']
		cairo_context.set_line_width(line_width)
		rgba = operation['rgba']
		cairo_context.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)
		if operation['use_dashes']:
			cairo_context.set_dash([2*line_width, 2*line_width])
		cairo_context.append_path(operation['path'])
		cairo_context.stroke()
