# line.py

from gi.repository import Gtk, Gdk, Gio, GLib
import cairo, math

from .tools import ToolTemplate

class ToolLine(ToolTemplate):
	__gtype_name__ = 'ToolLine'

	use_size = True
	implements_panel = False

	def __init__(self, window, **kwargs):
		super().__init__('line', _("Line"), 'list-remove-symbolic', window)

		self.add_tool_action_enum('line_type', 'straight', self.on_change_active_type)
		self.add_tool_action_enum('line_shape', 'round', self.on_change_active_shape)
		self.add_tool_action_boolean('line_dashes', False, self.set_dashes_state)
		self.add_tool_action_boolean('line_arrow', False, self.set_arrow_state)
		self.add_tool_action_enum('line_operator', 'over', self.on_change_active_operator)

		# Default values
		self.selected_shape_label = _("Round")
		self.selected_curv_label = _("Straight")
		self.active_type = 'line'
		self.selected_operator = cairo.Operator.OVER
		self.selected_end_id = cairo.LineCap.ROUND
		self.wait_points = (-1.0, -1.0, -1.0, -1.0)
		self.use_dashes = False
		self.use_arrow = False

	def set_dashes_state(self, *args):
		if not args[0].get_state():
			self.use_dashes = True
			args[0].set_state(GLib.Variant.new_boolean(True))
		else:
			self.use_dashes = False
			args[0].set_state(GLib.Variant.new_boolean(False))

	def set_arrow_state(self, *args):
		if not args[0].get_state():
			self.use_arrow = True
			args[0].set_state(GLib.Variant.new_boolean(True))
		else:
			self.use_arrow = False
			args[0].set_state(GLib.Variant.new_boolean(False))

	def on_change_active_shape(self, *args):
		state_as_string = args[1].get_string()
		if state_as_string == args[0].get_state().get_string():
			return
		args[0].set_state(GLib.Variant.new_string(state_as_string))
		if state_as_string == 'square':
			self.selected_end_id = cairo.LineCap.BUTT
			self.selected_shape_label = _("Square")
		else:
			self.selected_end_id = cairo.LineCap.ROUND
			self.selected_shape_label = _("Round")

	def on_change_active_type(self, *args):
		self.wait_points = (-1.0, -1.0, -1.0, -1.0)
		state_as_string = args[1].get_string()
		if state_as_string == args[0].get_state().get_string():
			return
		args[0].set_state(GLib.Variant.new_string(state_as_string))
		if state_as_string == 'straight':
			self.active_type = 'line'
			self.selected_curv_label = _("Straight")
		else:
			self.active_type = 'arc'
			self.selected_curv_label = _("Arc")

	def on_change_active_operator(self, *args):
		state_as_string = args[1].get_string()
		if state_as_string == args[0].get_state().get_string():
			return
		args[0].set_state(GLib.Variant.new_string(state_as_string))
		if state_as_string == 'difference':
			self.selected_operator = cairo.Operator.DIFFERENCE
			self.selected_operator_label = _("Difference")
		elif state_as_string == 'exclusion':
			self.selected_operator = cairo.Operator.EXCLUSION
			self.selected_operator_label = _("Exclusion")
		elif state_as_string == 'clear':
			self.selected_operator = cairo.Operator.CLEAR
			self.selected_operator_label = _("Eraser")
		else:
			self.selected_operator = cairo.Operator.OVER
			self.selected_operator_label = _("Classic")

	def get_options_model(self):
		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/Drawing/tools/ui/tool_line.ui')
		return builder.get_object('options-menu')

	def get_options_label(self):
		return self.selected_curv_label

	def get_edition_status(self):
		label = self.selected_curv_label + ' (' + self.selected_shape_label + ') '
		if self.use_arrow and self.use_dashes:
			label = label + ' - ' + _("Arrow") + ' - ' + _("With dashes")
		elif self.use_arrow:
			label = label + ' - ' + _("Arrow")
		elif self.use_dashes:
			label = label + ' - ' + _("With dashes")
		return label

	def give_back_control(self):
		if self.wait_points == (-1.0, -1.0, -1.0, -1.0):
			self.x_press = 0.0
			self.y_press = 0.0
			return False
		else:
			self.wait_points = (-1.0, -1.0, -1.0, -1.0)
			self.x_press = 0.0
			self.y_press = 0.0
			return True

	def on_motion_on_area(self, area, event, surface, event_x, event_y):
		self.restore_pixbuf()
		w_context = cairo.Context(self.get_surface())
		if self.active_type == 'line':
			w_context.move_to(self.x_press, self.y_press)
			w_context.line_to(event_x, event_y)
		elif self.active_type == 'arc':
			if self.wait_points == (-1.0, -1.0, -1.0, -1.0):
				w_context.move_to(self.x_press, self.y_press)
				w_context.line_to(event_x, event_y)
			else:
				w_context.move_to(self.wait_points[0], self.wait_points[1])
				w_context.curve_to(self.wait_points[2], self.wait_points[3], self.x_press, self.y_press, event_x, event_y)

		self._path = w_context.copy_path()
		operation = self.build_operation(event_x, event_y)
		self.do_tool_operation(operation)

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color, event_x, event_y):
		self.x_press = event_x
		self.y_press = event_y
		self.tool_width = tool_width
		if event.button == 1:
			self.main_color = left_color
		if event.button == 3:
			self.main_color = right_color

	def on_release_on_area(self, area, event, surface, event_x, event_y):
		if self.active_type == 'line':
			self.restore_pixbuf()
			w_context = cairo.Context(self.get_surface())
			w_context.move_to(self.x_press, self.y_press)
			w_context.line_to(event_x, event_y)

		elif self.active_type == 'arc':
			if self.wait_points == (-1.0, -1.0, -1.0, -1.0):
				self.wait_points = (self.x_press, self.y_press, event_x, event_y)
				return
			else:
				self.restore_pixbuf()
				w_context = cairo.Context(self.get_surface())
				w_context.move_to(self.wait_points[0], self.wait_points[1])
				w_context.curve_to(self.wait_points[2], self.wait_points[3], self.x_press, self.y_press, event_x, event_y)
				self.wait_points = (-1.0, -1.0, -1.0, -1.0)

		self._path = w_context.copy_path()
		operation = self.build_operation(event_x, event_y)
		self.apply_operation(operation)
		self.x_press = 0.0
		self.y_press = 0.0

	def add_arrow_triangle(self, w_context, x_release, y_release, x_press, y_press, line_width):
		w_context.new_path()
		w_context.set_line_width(line_width)
		w_context.set_dash([1, 0])
		w_context.move_to(x_release, y_release)
		x_length = max(x_press, x_release) - min(x_press, x_release)
		y_length = max(y_press, y_release) - min(y_press, y_release)
		line_length = math.sqrt( (x_length)**2 + (y_length)**2 )
		arrow_width = math.log(line_length)
		if (x_press - x_release) != 0:
			delta = (y_press - y_release) / (x_press - x_release)
		else:
			delta = 1.0

		x_backpoint = (x_press + x_release)/2
		y_backpoint = (y_press + y_release)/2
		i = 0
		while i < arrow_width:
			i = i + 2
			x_backpoint = (x_backpoint + x_release)/2
			y_backpoint = (y_backpoint + y_release)/2

		if delta < -1.5 or delta > 1.0:
			w_context.line_to(x_backpoint-arrow_width, y_backpoint)
			w_context.line_to(x_backpoint+arrow_width, y_backpoint)
		elif delta > -0.5 and delta <= 1.0:
			w_context.line_to(x_backpoint, y_backpoint-arrow_width)
			w_context.line_to(x_backpoint, y_backpoint+arrow_width)
		else:
			w_context.line_to(x_backpoint-arrow_width, y_backpoint-arrow_width)
			w_context.line_to(x_backpoint+arrow_width, y_backpoint+arrow_width)

		w_context.close_path()
		w_context.fill_preserve()
		w_context.stroke()

	def build_operation(self, event_x, event_y):
		operation = {
			'tool_id': self.id,
			'rgba': self.main_color,
			'operator': self.selected_operator,
			'line_width': self.tool_width,
			'line_cap': self.selected_end_id,
			'use_dashes': self.use_dashes,
			'use_arrow': self.use_arrow,
			'path': self._path,
			'x_release': event_x,
			'y_release': event_y,
			'x_press': self.x_press,
			'y_press': self.y_press
		}
		return operation

	def do_tool_operation(self, operation):
		if operation['tool_id'] != self.id:
			return
		self.restore_pixbuf()
		w_context = cairo.Context(self.get_surface())
		w_context.set_operator(operation['operator'])
		w_context.set_line_cap(operation['line_cap'])
		#w_context.set_line_join(operation['line_join'])
		line_width = operation['line_width']
		w_context.set_line_width(line_width)
		rgba = operation['rgba']
		w_context.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)
		if operation['use_dashes']:
			w_context.set_dash([2*line_width, 2*line_width])
		w_context.append_path(operation['path'])
		w_context.stroke()

		if operation['use_arrow']:
			x_press = operation['x_press']
			y_press = operation['y_press']
			x_release = operation['x_release']
			y_release = operation['y_release']
			self.add_arrow_triangle(w_context, x_release, y_release, x_press, y_press, line_width)
