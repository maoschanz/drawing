# tool_experiment.py

import cairo, math
from gi.repository import Gtk, Gdk

from .abstract_classic_tool import AbstractClassicTool
from .utilities_tools import utilities_smooth_path

class ToolExperiment(AbstractClassicTool):
	__gtype_name__ = 'ToolExperiment'

	def __init__(self, window, **kwargs):
		super().__init__('experiment', _("Experiment"), 'applications-utilities-symbolic', window)
		self.use_size = True
		self.row.get_style_context().add_class('destructive-action')
		self.past_x = -1.0
		self.past_y = -1.0
		self._path = None
		self.use_antialias = True

		self.selected_mode = 'smooth'
		self.selected_operator_label = "DIFFERENCE"
		self.selected_operator = cairo.Operator.DIFFERENCE

		self.add_tool_action_enum('experiment_operator', 'DIFFERENCE')
		self.add_tool_action_enum('experiment_mode', 'smooth')
		self.add_tool_action_simple('experiment_macro_scie', self.action_macro_scie)
		self.add_tool_action_boolean('experiment_antialias', self.use_antialias)

	def set_active_mode(self, *args):
		state_as_string = self.get_option_value('experiment_mode')
		self.selected_mode =  state_as_string

	def set_antialias(self, *args):
		self.use_antialias = self.get_option_value('experiment_antialias')

	def set_active_operator(self, *args):
		state_as_string = self.get_option_value('experiment_operator')
		if state_as_string == 'CLEAR':
			self.selected_operator = cairo.Operator.CLEAR
		elif state_as_string == 'SOURCE':
			self.selected_operator = cairo.Operator.SOURCE
		elif state_as_string == 'OVER':
			self.selected_operator = cairo.Operator.OVER
		elif state_as_string == 'IN':
			self.selected_operator = cairo.Operator.IN
		elif state_as_string == 'OUT':
			self.selected_operator = cairo.Operator.OUT
		elif state_as_string == 'ATOP':
			self.selected_operator = cairo.Operator.ATOP
		elif state_as_string == 'DEST':
			self.selected_operator = cairo.Operator.DEST
		elif state_as_string == 'DEST_OVER':
			self.selected_operator = cairo.Operator.DEST_OVER
		elif state_as_string == 'DEST_IN':
			self.selected_operator = cairo.Operator.DEST_IN
		elif state_as_string == 'DEST_OUT':
			self.selected_operator = cairo.Operator.DEST_OUT
		elif state_as_string == 'DEST_ATOP':
			self.selected_operator = cairo.Operator.DEST_ATOP
		elif state_as_string == 'XOR':
			self.selected_operator = cairo.Operator.XOR
		elif state_as_string == 'ADD':
			self.selected_operator = cairo.Operator.ADD
		elif state_as_string == 'SATURATE':
			self.selected_operator = cairo.Operator.SATURATE
		elif state_as_string == 'MULTIPLY':
			self.selected_operator = cairo.Operator.MULTIPLY
		elif state_as_string == 'SCREEN':
			self.selected_operator = cairo.Operator.SCREEN
		elif state_as_string == 'OVERLAY':
			self.selected_operator = cairo.Operator.OVERLAY
		elif state_as_string == 'DARKEN':
			self.selected_operator = cairo.Operator.DARKEN
		elif state_as_string == 'LIGHTEN':
			self.selected_operator = cairo.Operator.LIGHTEN
		elif state_as_string == 'COLOR_DODGE':
			self.selected_operator = cairo.Operator.COLOR_DODGE
		elif state_as_string == 'COLOR_BURN':
			self.selected_operator = cairo.Operator.COLOR_BURN
		elif state_as_string == 'HARD_LIGHT':
			self.selected_operator = cairo.Operator.HARD_LIGHT
		elif state_as_string == 'SOFT_LIGHT':
			self.selected_operator = cairo.Operator.SOFT_LIGHT
		elif state_as_string == 'DIFFERENCE':
			self.selected_operator = cairo.Operator.DIFFERENCE
		elif state_as_string == 'EXCLUSION':
			self.selected_operator = cairo.Operator.EXCLUSION
		elif state_as_string == 'HSL_HUE':
			self.selected_operator = cairo.Operator.HSL_HUE
		elif state_as_string == 'HSL_SATURATION':
			self.selected_operator = cairo.Operator.HSL_SATURATION
		elif state_as_string == 'HSL_COLOR':
			self.selected_operator = cairo.Operator.HSL_COLOR
		elif state_as_string == 'HSL_LUMINOSITY':
			self.selected_operator = cairo.Operator.HSL_LUMINOSITY
		self.selected_operator_label = state_as_string

	def action_macro_scie(self, *args):
		cairo_context = cairo.Context(self.get_surface())
		cairo_context.move_to(50, 50)
		cairo_context.line_to(100, 150)
		cairo_context.line_to(150, 50)
		cairo_context.line_to(200, 150)
		cairo_context.line_to(250, 50)
		cairo_context.line_to(300, 150)
		cairo_context.line_to(350, 50)
		cairo_context.line_to(400, 150)
		cairo_context.line_to(450, 50)
		cairo_context.line_to(500, 150)
		cairo_context.line_to(550, 50)
		self._path = cairo_context.copy_path()
		self.macros_common()

	def macros_common(self):
		self.set_common_values(1)
		operation = self.build_operation()
		self.apply_operation(operation)

	def get_options_label(self):
		self.set_active_operator()
		self.set_active_mode()
		self.set_antialias()
		if self.selected_mode == 'simple':
			return self.selected_operator_label
		else:
			return self.selected_mode

	def get_edition_status(self):
		return "You're not supposed to use this tool (development only)."

	def on_press_on_area(self, event, surface, event_x, event_y):
		self.set_active_operator()
		self.set_active_mode()
		self.set_antialias()
		self.x_press = event_x
		self.y_press = event_y
		self.set_common_values(event.button)

	def on_motion_on_area(self, event, surface, event_x, event_y):
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

	def on_release_on_area(self, event, surface, event_x, event_y):
		self.past_x = -1.0
		self.past_y = -1.0
		operation = self.build_operation()
		self.apply_operation(operation)

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'rgba': self.main_color,
			'operator': self.selected_operator,
			'mode': self.selected_mode,
			'line_width': self.tool_width,
			'line_cap': cairo.LineCap.ROUND,
			'line_join': cairo.LineJoin.ROUND,
			'antialias': self.use_antialias,
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
		if operation['antialias']:
			cairo_context.set_antialias(cairo.Antialias.DEFAULT)
		else:
			cairo_context.set_antialias(cairo.Antialias.NONE)

		if operation['mode'] == 'dynamic':
			self.op_dynamic(operation, cairo_context)
		elif operation['mode'] == 'smooth':
			self.op_simple(operation, cairo_context)
			self.op_smooth2(operation, cairo_context)
		else:
			self.op_simple(operation, cairo_context)

	def op_simple(self, operation, cairo_context):
		cairo_context.set_operator(operation['operator'])
		cairo_context.set_line_cap(operation['line_cap'])
		cairo_context.set_line_join(operation['line_join'])
		cairo_context.set_line_width(operation['line_width'])
		rgba = operation['rgba']
		cairo_context.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)
		cairo_context.append_path(operation['path'])
		cairo_context.stroke()

	def op_dynamic(self, operation, cairo_context):
		cairo_context.set_operator(cairo.Operator.SOURCE)
		cairo_context.set_line_cap(operation['line_cap'])
		cairo_context.set_line_join(operation['line_join'])
		rgba = operation['rgba']
		cairo_context.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)
		line_width = 0
		for pts in operation['path']:
			if pts[1] is ():
				continue
			current_x, current_y = cairo_context.get_current_point()
			future_x = pts[1][0]
			future_y = pts[1][1]
			dist = math.sqrt( (current_x - future_x) * (current_x - future_x) \
			                 + (current_y - future_y) * (current_y - future_y) )
			new_width = 1 + int( operation['line_width']/max(1, 0.05 * dist) )
			if line_width == 0:
				line_width = new_width
			else:
				line_width = (new_width + line_width) / 2
			# print(int(dist), line_width)
			cairo_context.set_line_width(line_width)
			cairo_context.line_to(int(future_x), int(future_y))
			cairo_context.stroke()
			cairo_context.move_to(int(future_x), int(future_y))

	def op_smooth2(self, operation, cairo_context):
		cairo_context.set_operator(cairo.Operator.OVER)
		cairo_context.set_line_width(operation['line_width'])
		cairo_context.set_line_cap(operation['line_cap'])
		cairo_context.set_line_join(operation['line_join'])
		rgba = operation['rgba']
		cairo_context.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)
		utilities_smooth_path(cairo_context, operation['path'])
		cairo_context.stroke()

	############################################################################
################################################################################

