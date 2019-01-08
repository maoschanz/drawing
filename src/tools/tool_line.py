# line.py

from gi.repository import Gtk, Gdk, Gio, GLib
import cairo, math

from .tools import ToolTemplate

class ToolLine(ToolTemplate):
	__gtype_name__ = 'ToolLine'

	use_size = True

	def __init__(self, window, **kwargs):
		super().__init__('line', _("Line"), 'list-remove-symbolic', window)

		self.add_tool_action_enum('line_type', 'straight', self.on_change_active_type)
		self.add_tool_action_enum('line_shape', 'round', self.on_change_active_shape)
		self.add_tool_action_boolean('line_dashes', False, self.set_dashes_state)
		self.add_tool_action_boolean('line_arrow', False, self.set_arrow_state)

		# Default values
		self.selected_shape_label = _("Round")
		self.selected_curv_label = _("Straight")
		self.active_type = 'line'
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
			self.use_dashes = False
			args[0].use_arrow(GLib.Variant.new_boolean(False))

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

	def get_options_model(self):
		builder = Gtk.Builder.new_from_resource("/com/github/maoschanz/Drawing/tools/ui/tool_line.ui")
		return builder.get_object('options-menu')

	def get_options_label(self):
		return self.selected_curv_label + ' - ' + self.selected_shape_label

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
		w_context = cairo.Context(self.window.get_surface())
		w_context.set_source_rgba(self.wanted_color.red, self.wanted_color.green, \
			self.wanted_color.blue, self.wanted_color.alpha)

		if self.use_dashes:
			w_context.set_dash([2*self.tool_width, 2*self.tool_width])

		if self.active_type == 'line':
			w_context.set_line_cap(self.selected_end_id)
			w_context.set_line_width(self.tool_width)
			w_context.move_to(self.x_press, self.y_press)
			w_context.line_to(event_x, event_y)
			w_context.stroke()

		elif self.active_type == 'arc':
			w_context.set_line_cap(self.selected_end_id)
			w_context.set_line_width(self.tool_width)
			if self.wait_points == (-1.0, -1.0, -1.0, -1.0):
				w_context.move_to(self.x_press, self.y_press)
				w_context.line_to(event_x, event_y)
				w_context.stroke()
			else:
				w_context.move_to(self.wait_points[0], self.wait_points[1])
				w_context.set_line_width(self.tool_width)
				w_context.curve_to(self.wait_points[2], self.wait_points[3], self.x_press, self.y_press, event_x, event_y)
				w_context.stroke()

		self.non_destructive_show_modif()

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color, event_x, event_y):
		self.x_press = event_x
		self.y_press = event_y
		self.tool_width = tool_width
		if event.button == 1:
			self.wanted_color = left_color
		if event.button == 3:
			self.wanted_color = right_color

	def on_release_on_area(self, area, event, surface, event_x, event_y):
		if self.active_type == 'line':
			self.restore_pixbuf()
			w_context = cairo.Context(self.window.get_surface())
			w_context.set_source_rgba(self.wanted_color.red, self.wanted_color.green, \
				self.wanted_color.blue, self.wanted_color.alpha)
			w_context.set_line_cap(self.selected_end_id)
			w_context.set_line_width(self.tool_width)
			if self.use_dashes:
				w_context.set_dash([2*self.tool_width, 2*self.tool_width])

			w_context.move_to(self.x_press, self.y_press)
			w_context.line_to(event_x, event_y)
			if self.use_arrow:
				self.add_arrow_triangle(w_context, event_x, event_y)
			w_context.stroke()
			self.apply_to_pixbuf()

		elif self.active_type == 'arc':
			if self.wait_points == (-1.0, -1.0, -1.0, -1.0):
				self.wait_points = (self.x_press, self.y_press, event_x, event_y)
			else:
				self.restore_pixbuf()
				w_context = cairo.Context(self.window.get_surface())
				w_context.set_source_rgba(self.wanted_color.red, self.wanted_color.green, \
					self.wanted_color.blue, self.wanted_color.alpha)
				if self.use_dashes:
					w_context.set_dash([2*self.tool_width, 2*self.tool_width])

				w_context.move_to(self.wait_points[0], self.wait_points[1])
				w_context.set_line_width(self.tool_width)
				w_context.set_line_cap(self.selected_end_id)
				w_context.curve_to(self.wait_points[2], self.wait_points[3], self.x_press, self.y_press, event_x, event_y)
				if self.use_arrow:
					self.add_arrow_triangle(w_context, event_x, event_y)
				w_context.stroke()
				self.wait_points = (-1.0, -1.0, -1.0, -1.0)
				self.apply_to_pixbuf()

		self.x_press = 0.0
		self.y_press = 0.0

	def add_arrow_triangle(self, w_context, eventx, eventy):
		w_context.stroke()
		w_context.set_dash([1, 0])
		w_context.move_to(eventx, eventy)
		x_length = max(self.x_press, eventx) - min(self.x_press, eventx)
		y_length = max(self.y_press, eventy) - min(self.y_press, eventy)
		line_length = math.sqrt( (x_length)**2 + (y_length)**2 )
		arrow_width = math.log(line_length)
		if (self.x_press - eventx) != 0:
			delta = (self.y_press - eventy) / (self.x_press - eventx)
		else:
			delta = 1.0

		x_backpoint = (self.x_press + eventx)/2
		y_backpoint = (self.y_press + eventy)/2
		i = 0
		while i < arrow_width:
			i = i + 2
			x_backpoint = (x_backpoint + eventx)/2
			y_backpoint = (y_backpoint + eventy)/2

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
