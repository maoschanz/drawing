# shape.py

from gi.repository import Gtk, Gdk, Gio, GLib
import cairo
import math

from .tools import ToolTemplate

class ToolShape(ToolTemplate):
	__gtype_name__ = 'ToolShape'

	use_size = True

	def __init__(self, window, **kwargs):
		super().__init__('shape', _("Basic shape"), 'radio-symbolic', window)

		(self.x_press, self.y_press) = (-1.0, -1.0)
		self.selected_style_label = _("Filled (secondary color)")
		self.selected_shape_label = _("Rectangle")
		self.selected_style_id = 'secondary'
		self.selected_shape_id = 'rectangle'

		# Building the widget containing options
		builder = Gtk.Builder.new_from_resource("/com/github/maoschanz/Drawing/tools/ui/shape.ui")
		self.options_menu_model = builder.get_object('options-menu')
		self.add_tool_action_enum('shape_shape', 'rectangle', self.on_change_active_shape)
		self.add_tool_action_enum('shape_style', 'secondary', self.on_change_active_style)

	def on_change_active_style(self, *args):
		state_as_string = args[1].get_string()
		if state_as_string == args[0].get_state().get_string():
			return
		args[0].set_state(GLib.Variant.new_string(state_as_string))
		self.selected_style_id = state_as_string
		if state_as_string == 'empty':
			self.selected_style_label = _("Empty")
		elif state_as_string == 'filled':
			self.selected_style_label = _("Filled (main color)")
		else:
			self.selected_style_label = _("Filled (secondary color)")
		self.window.set_picture_title()

	def on_change_active_shape(self, *args):
		state_as_string = args[1].get_string()
		if state_as_string == args[0].get_state().get_string():
			return
		args[0].set_state(GLib.Variant.new_string(state_as_string))
		self.selected_shape_id = state_as_string
		if state_as_string == 'rectangle':
			self.selected_shape_label = _("Rectangle")
		elif state_as_string == 'oval':
			self.selected_shape_label = _("Oval")
		else:
			self.selected_shape_label = _("Circle")
		self.window.set_picture_title()

	def get_options_model(self):
		builder = Gtk.Builder.new_from_resource("/com/github/maoschanz/Drawing/tools/ui/shape.ui")
		return builder.get_object('options-menu')

	def get_options_label(self):
		return self.selected_shape_label + ' - ' + self.selected_style_label

	def get_edition_status(self):
		label = self.label + ' -' + self.selected_shape_label + ' - ' + \
			self.selected_style_label
		return label

	def give_back_control(self):
		(self.x_press, self.y_press) = (-1.0, -1.0)
		self.restore_pixbuf()
		return False

	def draw_rectangle(self, event):
		w_context = cairo.Context(self.window.get_surface())
		w_context.set_line_width(self.tool_width)

		if self.selected_style_id == 'secondary':
			w_context.move_to(self.x_press, self.y_press)
			w_context.line_to(self.x_press, event.y)
			w_context.line_to(event.x, event.y)
			w_context.line_to(event.x, self.y_press)
			w_context.close_path()
			w_context.set_source_rgba(self.secondary_color.red, self.secondary_color.green, \
				self.secondary_color.blue, self.secondary_color.alpha)
			w_context.fill()
			w_context.stroke()
		w_context.set_source_rgba(self.main_color.red, self.main_color.green, \
			self.main_color.blue, self.main_color.alpha)
		w_context.move_to(self.x_press, self.y_press)
		w_context.line_to(self.x_press, event.y)
		w_context.line_to(event.x, event.y)
		w_context.line_to(event.x, self.y_press)
		w_context.close_path()

		if self.selected_style_id == 'filled':
			w_context.fill()
		w_context.stroke()

	def draw_oval(self, event):
		w_context = cairo.Context(self.window.get_surface())
		w_context.set_line_width(self.tool_width)

		if self.selected_style_id == 'secondary':
			w_context.curve_to(self.x_press, (self.y_press+event.y)/2, \
				self.x_press, event.y, \
				(self.x_press+event.x)/2, event.y)
			w_context.curve_to((self.x_press+event.x)/2, event.y, \
				event.x, event.y, \
				event.x, (self.y_press+event.y)/2)
			w_context.curve_to(event.x, (self.y_press+event.y)/2, \
				event.x, self.y_press, \
				(self.x_press+event.x)/2, self.y_press)
			w_context.curve_to((self.x_press+event.x)/2, self.y_press, \
				self.x_press, self.y_press, \
				self.x_press, (self.y_press+event.y)/2)
			w_context.close_path()
			w_context.set_source_rgba(self.secondary_color.red, self.secondary_color.green, \
				self.secondary_color.blue, self.secondary_color.alpha)
			w_context.fill()
			w_context.stroke()
		w_context.set_source_rgba(self.main_color.red, self.main_color.green, \
			self.main_color.blue, self.main_color.alpha)
		w_context.curve_to(self.x_press, (self.y_press+event.y)/2, \
			self.x_press, event.y, \
			(self.x_press+event.x)/2, event.y)
		w_context.curve_to((self.x_press+event.x)/2, event.y, \
			event.x, event.y, \
			event.x, (self.y_press+event.y)/2)
		w_context.curve_to(event.x, (self.y_press+event.y)/2, \
			event.x, self.y_press, \
			(self.x_press+event.x)/2, self.y_press)
		w_context.curve_to((self.x_press+event.x)/2, self.y_press, \
			self.x_press, self.y_press, \
			self.x_press, (self.y_press+event.y)/2)
		w_context.close_path()

		if self.selected_style_id == 'filled':
			w_context.fill()
		w_context.stroke()

	def draw_circle(self, event):
		w_context = cairo.Context(self.window.get_surface())
		w_context.set_line_width(self.tool_width)

		rayon = math.sqrt((self.x_press - event.x)*(self.x_press - event.x) \
			+ (self.y_press - event.y)*(self.y_press - event.y))

		if self.selected_style_id == 'secondary':
			w_context.new_sub_path()
			w_context.arc(self.x_press, self.y_press, rayon, 0.0, 2*math.pi)
			w_context.set_source_rgba(self.secondary_color.red, self.secondary_color.green, \
				self.secondary_color.blue, self.secondary_color.alpha)
			w_context.fill()
			w_context.stroke()
		w_context.set_source_rgba(self.main_color.red, self.main_color.green, \
			self.main_color.blue, self.main_color.alpha)

		w_context.new_sub_path()
		w_context.arc(self.x_press, self.y_press, rayon, 0.0, 2*math.pi)
		if self.selected_style_id == 'filled':
			w_context.fill()
		w_context.stroke()

	def on_motion_on_area(self, area, event, surface, event_x, event_y):
		self.restore_pixbuf()
		if self.selected_shape_id == 'rectangle':
			self.draw_rectangle(event)
		elif self.selected_shape_id == 'oval':
			self.draw_oval(event)
		elif self.selected_shape_id == 'circle':
			self.draw_circle(event)

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color, event_x, event_y):
		self.x_press = event.x
		self.y_press = event.y
		self.tool_width = tool_width
		if event.button == 3:
			self.main_color = right_color
			self.secondary_color = left_color
		else:
			self.main_color = left_color
			self.secondary_color = right_color

	def on_release_on_area(self, area, event, surface, event_x, event_y):
		if self.selected_shape_id == 'rectangle':
			self.restore_pixbuf()
			self.draw_rectangle(event)
			self.apply_to_pixbuf()
		elif self.selected_shape_id == 'oval':
			self.restore_pixbuf()
			self.draw_oval(event)
			self.apply_to_pixbuf()
		elif self.selected_shape_id == 'circle':
			self.restore_pixbuf()
			self.draw_circle(event)
			self.apply_to_pixbuf()
		self.x_press = 0.0
		self.y_press = 0.0

