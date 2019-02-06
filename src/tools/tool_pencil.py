# tool_pencil.py

from gi.repository import Gtk, Gdk, Gio, GLib
import cairo

from .tools import ToolTemplate

class ToolPencil(ToolTemplate):
	__gtype_name__ = 'ToolPencil'

	use_size = True
	implements_panel = False

	def __init__(self, window, **kwargs):
		super().__init__('pencil', _("Pencil"), 'tool-pencil-symbolic', window)
		self.past_x = -1.0
		self.past_y = -1.0
		self._path = None
		self.main_color = None

		self.selected_shape_label = _("Round")
		self.selected_cap_id = cairo.LineCap.ROUND
		self.selected_join_id = cairo.LineCap.ROUND
		self.selected_operator = cairo.Operator.OVER
		self.use_dashes = False

		self.add_tool_action_enum('pencil_shape', 'round', self.on_change_active_shape)
		self.add_tool_action_enum('pencil_operator', 'over', self.on_change_active_operator)
		self.add_tool_action_boolean('pencil_dashes', self.use_dashes, self.set_dashes_state)

	def set_dashes_state(self, *args):
		if not args[0].get_state():
			self.use_dashes = True
			args[0].set_state(GLib.Variant.new_boolean(True))
		else:
			self.use_dashes = False
			args[0].set_state(GLib.Variant.new_boolean(False))

	def on_change_active_shape(self, *args):
		state_as_string = args[1].get_string()
		if state_as_string == args[0].get_state().get_string():
			return
		args[0].set_state(GLib.Variant.new_string(state_as_string))
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
		builder = Gtk.Builder.new_from_resource("/com/github/maoschanz/Drawing/tools/ui/tool_pencil.ui")
		return builder.get_object('options-menu')

	def get_options_label(self):
		return self.selected_shape_label

	def on_motion_on_area(self, area, event, surface, event_x, event_y):
		w_context = cairo.Context(self.get_surface())
		if self.past_x == -1.0:
			(self.past_x, self.past_y) = (self.x_press, self.y_press)
			w_context.move_to(self.x_press, self.y_press)
			self._path = w_context.copy_path()
		else:
			w_context.append_path(self._path)
		w_context.line_to(event_x, event_y)
		self._path = w_context.copy_path()
		self.past_x = event_x
		self.past_y = event_y

		operation = self.build_operation()
		self.do_tool_operation(operation)

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color, event_x, event_y):
		self.x_press = event_x
		self.y_press = event_y
		self.tool_width = tool_width
		if event.button == 3:
			self.main_color = right_color
		else:
			self.main_color = left_color

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
		self.restore_pixbuf()
		w_context = cairo.Context(self.get_surface())
		w_context.set_operator(operation['operator'])
		w_context.set_line_cap(operation['line_cap'])
		w_context.set_line_join(operation['line_join'])
		line_width = operation['line_width']
		w_context.set_line_width(line_width)
		rgba = operation['rgba']
		w_context.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)
		if operation['use_dashes']:
			w_context.set_dash([2*line_width, 2*line_width])
		w_context.append_path(operation['path'])
		w_context.stroke()
