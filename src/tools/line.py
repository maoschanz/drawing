# line.py

from gi.repository import Gtk, Gdk, Gio
import cairo

from .tools import ToolTemplate

class ToolLine(ToolTemplate):
	__gtype_name__ = 'ToolLine'

	use_size = True
	type_btns = {}
	end_btns = {}

	def __init__(self, window, **kwargs):
		super().__init__('line', _("Line"), 'list-remove-symbolic', window)

		# Building the widget containing options
		builder = Gtk.Builder()
		builder.add_from_resource("/com/github/maoschanz/Drawing/tools/ui/line.ui")
		self.options_box = builder.get_object("options-menu")

		type_btn_1 = builder.get_object('type_btn_1')
		type_btn_2 = builder.get_object('type_btn_2')
		type_btn_1.connect('clicked', self.on_type_changed, 'line')
		type_btn_2.connect('clicked', self.on_type_changed, 'arc')

		end_btn_1 = builder.get_object('end_btn_1')
		end_btn_2 = builder.get_object('end_btn_2')
		# end_btn_3 = builder.get_object('end_btn_3')
		end_btn_1.connect('clicked', self.on_end_changed, cairo.LineCap.BUTT)
		end_btn_2.connect('clicked', self.on_end_changed, cairo.LineCap.ROUND)
		# end_btn_3.connect('clicked', self.on_end_changed, cairo.LineCap.SQUARE)

		self.arrow_switch = builder.get_object("arrow_switch")

		# Default values
		self.selected_shape_label = _("Round")
		self.selected_curv_label = _("Straight")
		self.active_type = 'line'
		self.selected_end_id = cairo.LineCap.ROUND
		self.wait_points = (-1.0, -1.0, -1.0, -1.0)

	def on_end_changed(self, *args):
		self.selected_shape_label = args[0].get_label()
		self.selected_end_id = args[1]

	def on_type_changed(self, *args):
		self.selected_curv_label = args[0].get_label()
		self.wait_points = (-1.0, -1.0, -1.0, -1.0)
		self.active_type = args[1]

	def get_options_widget(self):
		return self.options_box

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

	def on_motion_on_area(self, area, event, surface):
		self.restore_pixbuf()
		w_context = cairo.Context(self.window.get_surface())
		w_context.set_source_rgba(self.wanted_color.red, self.wanted_color.green, \
			self.wanted_color.blue, self.wanted_color.alpha)

		if self.active_type == 'line':
			w_context.set_line_cap(self.selected_end_id)
			w_context.set_line_width(self.tool_width)
			w_context.move_to(self.x_press, self.y_press)
			w_context.line_to(event.x, event.y)
			w_context.stroke()

		elif self.active_type == 'arc':
			w_context.set_line_cap(self.selected_end_id)
			w_context.set_line_width(self.tool_width)

			if self.wait_points == (-1.0, -1.0, -1.0, -1.0):
				w_context.move_to(self.x_press, self.y_press)
				w_context.line_to(event.x, event.y)
				w_context.stroke()
			else:
				w_context.move_to(self.wait_points[0], self.wait_points[1])
				w_context.set_line_width(self.tool_width)
				w_context.curve_to(self.wait_points[2], self.wait_points[3], self.x_press, self.y_press, event.x, event.y)
				w_context.stroke()

		self.non_destructive_show_modif()

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color):
		self.x_press = event.x
		self.y_press = event.y
		self.tool_width = tool_width
		if event.button == 1:
			self.wanted_color = left_color
		if event.button == 3:
			self.wanted_color = right_color

	def on_release_on_area(self, area, event, surface):
		if self.active_type == 'line':
			self.restore_pixbuf()
			w_context = cairo.Context(self.window.get_surface())
			w_context.set_source_rgba(self.wanted_color.red, self.wanted_color.green, \
				self.wanted_color.blue, self.wanted_color.alpha)
			w_context.set_line_cap(self.selected_end_id)
			w_context.set_line_width(self.tool_width)
			w_context.move_to(self.x_press, self.y_press)
			w_context.line_to(event.x, event.y)
			w_context.stroke()
			self.apply_to_pixbuf()

		elif self.active_type == 'arc':
			if self.wait_points == (-1.0, -1.0, -1.0, -1.0):
				self.wait_points = (self.x_press, self.y_press, event.x, event.y)
			else:
				self.restore_pixbuf()
				w_context = cairo.Context(self.window.get_surface())
				w_context.set_source_rgba(self.wanted_color.red, self.wanted_color.green, \
					self.wanted_color.blue, self.wanted_color.alpha)

				w_context.move_to(self.wait_points[0], self.wait_points[1])
				w_context.set_line_width(self.tool_width)
				w_context.set_line_cap(self.selected_end_id)
				w_context.curve_to(self.wait_points[2], self.wait_points[3], self.x_press, self.y_press, event.x, event.y)
				w_context.stroke()
				self.wait_points = (-1.0, -1.0, -1.0, -1.0)
				self.apply_to_pixbuf()

		if self.arrow_switch.get_active():
			print("arrow") # TODO

		self.x_press = 0.0
		self.y_press = 0.0
