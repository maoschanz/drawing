# shape.py

from gi.repository import Gtk, Gdk, Gio
import cairo
import math

from .tools import ToolTemplate

class ToolShape(ToolTemplate):
	__gtype_name__ = 'ToolShape'

	use_options = True
	window_can_take_back_control = True
	use_size = True
	set_clip = False
	shape_btns = {}
	style_btns = {}

	def __init__(self, window, **kwargs):
		super().__init__('shape', _("Shape"), 'non-starred-symbolic', window)

		self.past_x = -1.0
		self.past_y = -1.0

		# Building the widget containing options
		builder = Gtk.Builder()
		builder.add_from_resource("/com/github/maoschanz/Drawing/tools/ui/shape.ui")
		self.options_box = builder.get_object("options_box")

		self.shape_btns['rectangle'] = builder.get_object("type_btn_1")
		self.shape_btns['rounded'] = builder.get_object("type_btn_2")
		self.shape_btns['ellipsis'] = builder.get_object("type_btn_3")
		self.shape_btns['circle'] = builder.get_object("type_btn_4")
		self.shape_btns['polygon'] = builder.get_object("type_btn_5")

		for type_id in self.shape_btns:
			self.shape_btns[type_id].connect('clicked', self.on_shape_changed)

		self.style_btns['empty'] = builder.get_object("style_btn_1")
		self.style_btns['filled'] = builder.get_object("style_btn_2")
		self.style_btns['secondary'] = builder.get_object("style_btn_3")

		for type_id in self.style_btns:
			self.style_btns[type_id].connect('clicked', self.on_style_changed)

		self.shape_btns['rectangle'].set_active(True)
		self.style_btns['secondary'].set_active(True)

		self.selected_shape = _("Rectangle") # FIXME
		self.selected_style = _("Filled (secondary color)") # FIXME


	def active_shape(self):
		for type_id in self.shape_btns:
			if self.shape_btns[type_id].get_active():
				return type_id
		return 'rectangle'

	def active_style(self):
		for type_id in self.style_btns:
			if self.style_btns[type_id].get_active():
				return type_id
		return 'empty'

	def on_shape_changed(self, b):
		self.selected_shape = b.get_label()

	def on_style_changed(self, b):
		self.selected_style = b.get_label()

	def get_options_widget(self):
		return self.options_box

	def get_options_label(self):
		return self.selected_shape + ' - ' + self.selected_style

	def give_back_control(self):
		pass

	def draw_rectangle(self, event):
		w_context = cairo.Context(self.window._surface)
		w_context.set_line_width(self.tool_width)

		if self.active_style() == 'secondary':
			w_context.move_to(self.x_press, self.y_press)
			w_context.line_to(self.x_press, event.y)
			w_context.line_to(event.x, event.y)
			w_context.line_to(event.x, self.y_press)
			w_context.close_path()
			w_context.set_source_rgba(self.secondary_color.red, self.secondary_color.green, \
				self.secondary_color.blue, self.secondary_color.alpha)
			w_context.fill()
			w_context.stroke()
		w_context.set_source_rgba(self.primary_color.red, self.primary_color.green, \
			self.primary_color.blue, self.primary_color.alpha)
		w_context.move_to(self.x_press, self.y_press)
		w_context.line_to(self.x_press, event.y)
		w_context.line_to(event.x, event.y)
		w_context.line_to(event.x, self.y_press)
		w_context.close_path()

		if self.active_style() == 'filled':
			w_context.fill()
		w_context.stroke()

	def draw_rounded(self, event):
		w_context = cairo.Context(self.window._surface)
		w_context.set_line_width(self.tool_width)

		if self.active_style() == 'secondary':
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
		w_context.set_source_rgba(self.primary_color.red, self.primary_color.green, \
			self.primary_color.blue, self.primary_color.alpha)
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

		if self.active_style() == 'filled':
			w_context.fill()
		w_context.stroke()

	def draw_ellipsis(self, event): # TODO
		pass

	def draw_circle(self, event):
		w_context = cairo.Context(self.window._surface)
		w_context.set_line_width(self.tool_width)

		rayon = math.sqrt((self.x_press - event.x)*(self.x_press - event.x) \
			+ (self.y_press - event.y)*(self.y_press - event.y))

		if self.active_style() == 'secondary':
			w_context.new_sub_path()
			w_context.arc(self.x_press, self.y_press, rayon, 0.0, 2*math.pi)
			w_context.set_source_rgba(self.secondary_color.red, self.secondary_color.green, \
				self.secondary_color.blue, self.secondary_color.alpha)
			w_context.fill()
			w_context.stroke()
		w_context.set_source_rgba(self.primary_color.red, self.primary_color.green, \
			self.primary_color.blue, self.primary_color.alpha)

		w_context.new_sub_path()
		w_context.arc(self.x_press, self.y_press, rayon, 0.0, 2*math.pi)
		if self.active_style() == 'filled':
			w_context.fill()
		w_context.stroke()

	def draw_polygon(self, event):
		self.draw_polygon_temp(event)
		# TODO particulier lui

	def on_key_on_area(self, area, event, surface):
		print("key")

	def on_motion_on_area(self, area, event, surface):
		self.window.use_stable_pixbuf()
		w_context = cairo.Context(self.window._surface)

		if self.active_shape() == 'rectangle':
			self.draw_rectangle(event)

		elif self.active_shape() == 'rounded':
			self.draw_rounded(event)

		elif self.active_shape() == 'ellipsis': # FIXME

			######################################"

			w_context.set_line_width(self.tool_width)

			rayon = math.sqrt((self.x_press - event.x)*(self.x_press - event.x) \
				+ (self.y_press - event.y)*(self.y_press - event.y))

			w_context.save()
			width = abs(self.x_press - event.x)
			height = abs(self.y_press - event.y)
			if width > height:
				scale_x = 1
				scale_y = height/width
			else:
				scale_x = width/height
				scale_y = 1
			scale_x = scale_x/2
			scale_y = scale_y/2
			# w_context.translate(-1 * min(self.x_press, event.x) * scale_x + width, -1 * min(self.y_press, event.y) * scale_y + self.y_press + height)
			w_context.scale(scale_x, scale_y)

			center_x = (self.x_press + event.x)/2
			center_y = (self.y_press + event.y)/2

			if self.active_style() == 'secondary':
				w_context.new_sub_path()
				w_context.arc(center_x, center_y, rayon, 0.0, 2*math.pi)
				w_context.set_source_rgba(self.secondary_color.red, self.secondary_color.green, \
					self.secondary_color.blue, self.secondary_color.alpha)
				w_context.fill()
				w_context.stroke()
			w_context.set_source_rgba(self.primary_color.red, self.primary_color.green, \
				self.primary_color.blue, self.primary_color.alpha)

			w_context.restore()

			w_context.new_sub_path()
			w_context.arc(self.x_press, self.y_press, rayon, 0.0, 2*math.pi)
			if self.active_style() == 'filled':
				w_context.fill()
			w_context.stroke()

			# w_context.restore()

			############################################

		elif self.active_shape() == 'circle':
			self.draw_circle(event)

		elif self.active_shape() == 'polygon': # TODO
			# self.draw_polygon(event)
			pass

		self.window.drawing_area.queue_draw()

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color):
		print("press")
		self.window_can_take_back_control = False

		self.x_press = event.x
		self.y_press = event.y
		self.tool_width = tool_width
		if event.button == 3:
			self.primary_color = right_color
			self.secondary_color = left_color
		else:
			self.primary_color = left_color
			self.secondary_color = right_color

	def on_release_on_area(self, area, event, surface):
		if self.active_shape() == 'rectangle':
			self.window.use_stable_pixbuf()
			self.draw_rectangle(event)
			self.window_can_take_back_control = True

		elif self.active_shape() == 'rounded':
			self.window.use_stable_pixbuf()
			self.draw_rounded(event)
			self.window_can_take_back_control = True

		elif self.active_shape() == 'ellipsis':
			self.window.use_stable_pixbuf()
			# self.draw_ellipsis(event)
			self.window_can_take_back_control = True

		elif self.active_shape() == 'circle':
			self.window.use_stable_pixbuf()
			self.draw_circle(event)
			self.window_can_take_back_control = True

		elif self.active_shape() == 'polygon':
			self.window.use_stable_pixbuf()
			self.draw_polygon(event)
			self.window_can_take_back_control = True



		self.x_press = 0.0
		self.y_press = 0.0
		# self.past_x = -1.0
		# self.past_y = -1.0


	def draw_polygon_temp(self, event):
		w_context = cairo.Context(self.window._surface)
		w_context.set_line_width(self.tool_width)

		if self.past_x == -1.0:
			(self.past_x, self.past_y) = (self.x_press, self.y_press)
			w_context.move_to(self.x_press, self.y_press)
			self.path = w_context.copy_path()
		else:
			w_context.append_path(self.path)

		if (event.x - self.past_x < self.tool_width) and (event.y - self.past_y < self.tool_width):
			print("stroke")
			w_context.close_path()
			if self.active_style() == 'filled':
				w_context.fill()
			elif self.active_style() == 'secondary':
				w_context.set_source_rgba(self.secondary_color.red, self.secondary_color.green, \
					self.secondary_color.blue, self.secondary_color.alpha)
				w_context.fill_preserve() # TODO c'est élégant ça, je devrais le faire ailleurs
				w_context.set_source_rgba(self.primary_color.red, self.primary_color.green, \
					self.primary_color.blue, self.primary_color.alpha)
				w_context.stroke()
			else:
				w_context.stroke()
			(self.past_x, self.past_y) = (-1.0, -1.0)

			self.window_can_take_back_control = True

		else:
			w_context.line_to(event.x, event.y)
			w_context.stroke_preserve() # draw the line without closing the path
			self.path = w_context.copy_path()

