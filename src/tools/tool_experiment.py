# tool_experiment.py

from gi.repository import Gtk, Gdk
import cairo

from .abstract_tool import ToolTemplate

class ToolExperiment(ToolTemplate):
	__gtype_name__ = 'ToolExperiment'

	def __init__(self, window, **kwargs):
		super().__init__('experiment', _("Experiment"), 'applications-science-symbolic', window)
		self.past_x = -1.0
		self.past_y = -1.0
		self._path = None
		self.main_color = None
		self.use_size = True

		self.selected_operator_label = "DIFFERENCE"
		self.selected_operator = cairo.Operator.DIFFERENCE

		self.add_tool_action_enum('experiment_operator', 'DIFFERENCE')

	def set_active_operator(self, *args):
		state_as_string = self.get_option_value('experiment_operator')
		if state_as_string == 'CLEAR':
			self.selected_operator = cairo.Operator.CLEAR
			self.selected_operator_label = "CLEAR"
		elif state_as_string == 'SOURCE':
			self.selected_operator = cairo.Operator.SOURCE
			self.selected_operator_label = "SOURCE"
		elif state_as_string == 'OVER':
			self.selected_operator = cairo.Operator.OVER
			self.selected_operator_label = "OVER"
		elif state_as_string == 'IN':
			self.selected_operator = cairo.Operator.IN
			self.selected_operator_label = "IN"
		elif state_as_string == 'OUT':
			self.selected_operator = cairo.Operator.OUT
			self.selected_operator_label = "OUT"
		elif state_as_string == 'ATOP':
			self.selected_operator = cairo.Operator.ATOP
			self.selected_operator_label = "ATOP"
		elif state_as_string == 'DEST':
			self.selected_operator = cairo.Operator.DEST
			self.selected_operator_label = "DEST"
		elif state_as_string == 'DEST_OVER':
			self.selected_operator = cairo.Operator.DEST_OVER
			self.selected_operator_label = "DEST_OVER"
		elif state_as_string == 'DEST_IN':
			self.selected_operator = cairo.Operator.DEST_IN
			self.selected_operator_label = "DEST_IN"
		elif state_as_string == 'DEST_OUT':
			self.selected_operator = cairo.Operator.DEST_OUT
			self.selected_operator_label = "DEST_OUT"
		elif state_as_string == 'DEST_ATOP':
			self.selected_operator = cairo.Operator.DEST_ATOP
			self.selected_operator_label = "DEST_ATOP"
		elif state_as_string == 'XOR':
			self.selected_operator = cairo.Operator.XOR
			self.selected_operator_label = "XOR"
		elif state_as_string == 'ADD':
			self.selected_operator = cairo.Operator.ADD
			self.selected_operator_label = "ADD"
		elif state_as_string == 'SATURATE':
			self.selected_operator = cairo.Operator.SATURATE
			self.selected_operator_label = "SATURATE"
		elif state_as_string == 'MULTIPLY':
			self.selected_operator = cairo.Operator.MULTIPLY
			self.selected_operator_label = "MULTIPLY"
		elif state_as_string == 'SCREEN':
			self.selected_operator = cairo.Operator.SCREEN
			self.selected_operator_label = "SCREEN"
		elif state_as_string == 'OVERLAY':
			self.selected_operator = cairo.Operator.OVERLAY
			self.selected_operator_label = "OVERLAY"
		elif state_as_string == 'DARKEN':
			self.selected_operator = cairo.Operator.DARKEN
			self.selected_operator_label = "DARKEN"
		elif state_as_string == 'LIGHTEN':
			self.selected_operator = cairo.Operator.LIGHTEN
			self.selected_operator_label = "LIGHTEN"
		elif state_as_string == 'COLOR_DODGE':
			self.selected_operator = cairo.Operator.COLOR_DODGE
			self.selected_operator_label = "COLOR_DODGE"
		elif state_as_string == 'COLOR_BURN':
			self.selected_operator = cairo.Operator.COLOR_BURN
			self.selected_operator_label = "COLOR_BURN"
		elif state_as_string == 'HARD_LIGHT':
			self.selected_operator = cairo.Operator.HARD_LIGHT
			self.selected_operator_label = "HARD_LIGHT"
		elif state_as_string == 'SOFT_LIGHT':
			self.selected_operator = cairo.Operator.SOFT_LIGHT
			self.selected_operator_label = "SOFT_LIGHT"
		elif state_as_string == 'DIFFERENCE':
			self.selected_operator = cairo.Operator.DIFFERENCE
			self.selected_operator_label = "DIFFERENCE"
		elif state_as_string == 'EXCLUSION':
			self.selected_operator = cairo.Operator.EXCLUSION
			self.selected_operator_label = "EXCLUSION"
		elif state_as_string == 'HSL_HUE':
			self.selected_operator = cairo.Operator.HSL_HUE
			self.selected_operator_label = "HSL_HUE"
		elif state_as_string == 'HSL_SATURATION':
			self.selected_operator = cairo.Operator.HSL_SATURATION
			self.selected_operator_label = "HSL_SATURATION"
		elif state_as_string == 'HSL_COLOR':
			self.selected_operator = cairo.Operator.HSL_COLOR
			self.selected_operator_label = "HSL_COLOR"
		elif state_as_string == 'HSL_LUMINOSITY':
			self.selected_operator = cairo.Operator.HSL_LUMINOSITY
			self.selected_operator_label = "HSL_LUMINOSITY"

	def get_options_label(self):
		return self.selected_operator_label

	def get_edition_status(self):
		return self.selected_operator_label

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color, event_x, event_y):
		self.x_press = event_x
		self.y_press = event_y
		self.tool_width = tool_width
		if event.button == 3:
			self.main_color = right_color
		else:
			self.main_color = left_color
		self.set_active_operator()

	def on_motion_on_area(self, area, event, surface, event_x, event_y):
		self.restore_pixbuf()
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
			'line_cap': cairo.LineCap.ROUND,
			'line_join': cairo.LineJoin.ROUND,
			'path': self._path
		}
		return operation

	def do_tool_operation(self, operation):
		if operation['tool_id'] != self.id:
			return
		if operation['path'] is None:
			return
		self.restore_pixbuf()
		print(operation['operator'])
		cairo_context = cairo.Context(self.get_surface())
		cairo_context.set_operator(operation['operator'])
		cairo_context.set_line_cap(operation['line_cap'])
		cairo_context.set_line_join(operation['line_join'])
		line_width = operation['line_width']
		cairo_context.set_line_width(line_width)
		rgba = operation['rgba']
		cairo_context.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)
		cairo_context.append_path(operation['path'])
		cairo_context.stroke()
