# shape.py

from gi.repository import Gtk, Gdk, Gio
import cairo
import math

from .tools import ToolTemplate

class ToolShape(ToolTemplate):
	__gtype_name__ = 'ToolShape'

	use_size = True
	shape_btns = {}
	style_btns = {}
	selected_shape_label = ''
	selected_shape_id = 'rectangle'
	selected_style_label = ''
	selected_style_id = 'secondary'

	def __init__(self, window, **kwargs):
		super().__init__('shape', _("Basic shape"), 'radio-symbolic', window)

		(self.x_press, self.y_press) = (-1.0, -1.0)

		# Building the widget containing options
		builder = Gtk.Builder()
		builder.add_from_resource('/com/github/maoschanz/Drawing/tools/ui/shape.ui')
		self.options_box = builder.get_object('options_box')

		self.shape_btns['rectangle'] = builder.get_object('type_btn_1')
		self.shape_btns['oval'] = builder.get_object('type_btn_2')
		self.shape_btns['circle'] = builder.get_object('type_btn_4')

		for type_id in self.shape_btns:
			self.shape_btns[type_id].connect('toggled', self.on_shape_changed, type_id)

		self.style_btns['empty'] = builder.get_object('style_btn_1')
		self.style_btns['filled'] = builder.get_object('style_btn_2')
		self.style_btns['secondary'] = builder.get_object('style_btn_3')

		for type_id in self.style_btns:
			self.style_btns[type_id].connect('toggled', self.on_style_changed, type_id)

		self.shape_btns['rectangle'].set_active(True)
		self.style_btns['secondary'].set_active(True)

	def on_shape_changed(self, *args):
		self.selected_shape_label = args[0].get_label()
		self.selected_shape_id = args[1]

	def on_style_changed(self, *args):
		self.selected_style_label = args[0].get_label()
		self.selected_style_id = args[1]

	def get_options_widget(self):
		return self.options_box

	def get_options_label(self):
		return self.selected_shape_label + ' - ' + self.selected_style_label

	def give_back_control(self):
		(self.x_press, self.y_press) = (-1.0, -1.0)
		self.restore_pixbuf()

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

	def on_motion_on_area(self, area, event, surface):
		self.restore_pixbuf()
		if self.selected_shape_id == 'rectangle':
			self.draw_rectangle(event)
		elif self.selected_shape_id == 'oval':
			self.draw_oval(event)
		elif self.selected_shape_id == 'circle':
			self.draw_circle(event)

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color):
		self.x_press = event.x
		self.y_press = event.y
		self.tool_width = tool_width
		if event.button == 3:
			self.main_color = right_color
			self.secondary_color = left_color
		else:
			self.main_color = left_color
			self.secondary_color = right_color

	def on_release_on_area(self, area, event, surface):
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

