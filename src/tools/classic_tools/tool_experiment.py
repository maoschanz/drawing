# tool_experiment.py

from gi.repository import Gtk, Gdk
import cairo, math

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

		self.selected_mode = 'smooth2'
		self.selected_operator_label = "DIFFERENCE"
		self.selected_operator = cairo.Operator.DIFFERENCE

		self.add_tool_action_enum('experiment_operator', 'DIFFERENCE')
		self.add_tool_action_enum('experiment_mode', 'smooth2')
		self.add_tool_action_simple('experiment_macro_z', self.action_macro_z)
		self.add_tool_action_simple('experiment_macro_scie', self.action_macro_scie)
		self.add_tool_action_simple('experiment_macro_hexa1', self.action_macro_hexa1)
		self.add_tool_action_simple('experiment_macro_hexa2', self.action_macro_hexa2)

	def set_active_mode(self, *args):
		state_as_string = self.get_option_value('experiment_mode')
		self.selected_mode =  state_as_string

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

	def action_macro_z(self, *args):
		cairo_context = cairo.Context(self.get_surface())
		cairo_context.move_to(200, 200)
		cairo_context.line_to(400, 200)
		cairo_context.line_to(200, 400)
		cairo_context.line_to(400, 400)
		self._path = cairo_context.copy_path()
		self.macros_common()

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

	def action_macro_hexa1(self, *args):
		cairo_context = cairo.Context(self.get_surface())
		cairo_context.move_to(100, 300)
		cairo_context.line_to(200, 300)
		cairo_context.line_to(250, 400)
		cairo_context.line_to(200, 500)
		cairo_context.line_to(100, 500)
		cairo_context.line_to(50, 400)
		cairo_context.line_to(100, 300)
		self._path = cairo_context.copy_path()
		self.macros_common()

	def action_macro_hexa2(self, *args):
		cairo_context = cairo.Context(self.get_surface())
		cairo_context.move_to(500, 300)
		cairo_context.line_to(450, 400)
		cairo_context.line_to(500, 500)
		cairo_context.line_to(600, 500)
		cairo_context.line_to(650, 400)
		cairo_context.line_to(600, 300)
		cairo_context.line_to(500, 300)
		self._path = cairo_context.copy_path()
		self.macros_common()

	def macros_common(self):
		self.tool_width = self.window.thickness_spinbtn.get_value()
		self.main_color = self.get_image().get_left_rgba()
		operation = self.build_operation()
		self.apply_operation(operation)

	def get_options_label(self):
		self.set_active_operator()
		self.set_active_mode()
		if self.selected_mode == 'simple':
			return self.selected_operator_label
		else:
			return self.selected_mode

	def get_edition_status(self):
		return "You're not supposed to use this tool (development only)."

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color, event_x, event_y):
		self.set_active_operator()
		self.set_active_mode()
		self.x_press = event_x
		self.y_press = event_y
		self.tool_width = tool_width
		if event.button == 3:
			self.main_color = right_color
		else:
			self.main_color = left_color

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
			'mode': self.selected_mode,
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
		if operation['mode'] == 'dynamic':
			self.op_dynamic(operation)
		elif operation['mode'] == 'smooth1':
			self.op_simple(operation)
			self.op_smooth1(operation)
		elif operation['mode'] == 'smooth2':
			self.op_simple(operation)
			self.op_smooth2(operation)
		else:
			self.op_simple(operation)

	def op_simple(self, operation):
		if operation['tool_id'] != self.id:
			return
		if operation['path'] is None:
			return
		self.restore_pixbuf()
		cairo_context = cairo.Context(self.get_surface())
		cairo_context.set_operator(operation['operator'])
		cairo_context.set_line_cap(operation['line_cap'])
		cairo_context.set_line_join(operation['line_join'])
		cairo_context.set_line_width(operation['line_width'])
		rgba = operation['rgba']
		cairo_context.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)
		cairo_context.append_path(operation['path'])
		cairo_context.stroke()

	def op_dynamic(self, operation):
		if operation['tool_id'] != self.id:
			return
		if operation['path'] is None:
			return
		self.restore_pixbuf()
		cairo_context = cairo.Context(self.get_surface())
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

	def op_smooth1(self, operation):
		if operation['tool_id'] != self.id:
			return
		if operation['path'] is None:
			return
		# self.restore_pixbuf()
		cairo_context = cairo.Context(self.get_surface())
		cairo_context.set_operator(cairo.Operator.OVER)
		cairo_context.set_line_width(operation['line_width'])
		cairo_context.set_line_cap(operation['line_cap'])
		cairo_context.set_line_join(operation['line_join'])
		rgba = operation['rgba']
		cairo_context.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)

		past_x = None
		past_y = None
		current_x = None
		current_y = None
		future_x = None
		future_y = None
		for pts in operation['path']: # FIXME c'est de la merde mais osef
			if pts[1] is ():
				continue
			if past_x is None:
				past_x = int(pts[1][0])
				past_y = int(pts[1][1])
			elif current_x is None:
				current_x = int(pts[1][0])
				current_y = int(pts[1][1])
			else: # if future_x is None:
				future_x = int(pts[1][0])
				future_y = int(pts[1][1])
				cairo_context.curve_to(past_x, past_y, current_x, current_y, future_x, future_y)
				past_x = None
				past_y = None
				current_x = None
				current_y = None
				future_x = None
				future_y = None
		if past_x is not None:
			if current_x is None:
				cairo_context.line_to(past_x, past_y)
			else:
				cairo_context.curve_to(past_x, past_y, current_x, current_y, current_x, current_y)
		cairo_context.stroke()

	def op_smooth2(self, operation):
		if operation['tool_id'] != self.id:
			return
		if operation['path'] is None:
			return
		# self.restore_pixbuf()
		cairo_context = cairo.Context(self.get_surface())
		cairo_context.set_operator(cairo.Operator.OVER)
		cairo_context.set_line_width(operation['line_width'])
		cairo_context.set_line_cap(operation['line_cap'])
		cairo_context.set_line_join(operation['line_join'])
		rgba = operation['rgba']
		cairo_context.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)

		x1 = None
		y1 = None
		x2 = None
		y2 = None
		x3 = None
		y3 = None
		x4 = None
		y4 = None
		for pts in operation['path']:
			if pts[1] is ():
				continue
			x1, y1, x2, y2, x3, y3, x4, y4 = self.next_arc(cairo_context, \
			                       x2, y2, x3, y3, x4, y4, pts[1][0], pts[1][1])
		self.next_arc(cairo_context, x2, y2, x3, y3, x4, y4, None, None)
		cairo_context.stroke()

	def next_point(self, x1, y1, x2, y2, dist):
		coef = 0.1
		dx = x2 - x1
		dy = y2 - y1
		angle = math.atan2(dy, dx)
		nx = x2 + math.cos(angle) * dist * coef
		ny = y2 + math.sin(angle) * dist * coef
		return nx, ny

	def next_arc(self, cairo_context, x1, y1, x2, y2, x3, y3, x4, y4):
		if x2 is None or x3 is None:
			# No drawing possible yet, just continue to the next point
			return x1, y1, x2, y2, x3, y3, x4, y4
		dist = math.sqrt( (x2 - x3) * (x2 - x3) + (y2 - y3) * (y2 - y3) )
		if x1 is None and x4 is None:
			cairo_context.move_to(x2, y2)
			cairo_context.line_to(x3, y3)
			return x1, y1, x2, y2, x3, y3, x4, y4
		elif x1 is None:
			nx1, ny1 = x2, y2
			nx2, ny2 = self.next_point(x4, y4, x3, y3, dist)
		elif x4 is None:
			nx1, ny1 = self.next_point(x1, y1, x2, y2, dist)
			nx2, ny2 = x3, y3
		else:
			nx1, ny1 = self.next_point(x1, y1, x2, y2, dist)
			nx2, ny2 = self.next_point(x4, y4, x3, y3, dist)
		cairo_context.move_to(x2, y2)
		cairo_context.curve_to(nx1, ny1, nx2, ny2, x3, y3)
		return x1, y1, x2, y2, x3, y3, x4, y4



