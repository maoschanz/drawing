# line.py

from gi.repository import Gtk, Gdk, Gio
import cairo

from .tools import ToolTemplate

class ToolLine(ToolTemplate):
	__gtype_name__ = 'ToolLine'

	id = 'line'
	icon_name = 'list-remove-symbolic'
	label = _("Line")
	use_options = True
	window_can_take_back_control = True
	use_size = True
	set_clip = False
	type_btns = {}
	end_btns = {}

	def __init__(self, window, **kwargs):
		super().__init__(window)

		# Building the widget containing options
		builder = Gtk.Builder()
		builder.add_from_resource("/com/github/maoschanz/Draw/tools/ui/line.ui")
		self.options_box = builder.get_object("options_box")

		self.type_btns['line'] = builder.get_object("type_btn_1")
		self.type_btns['arc'] = builder.get_object("type_btn_2")

		for type_id in self.type_btns:
			self.type_btns[type_id].connect('clicked', self.on_type_changed)

		self.end_btns['none'] = builder.get_object("end_btn_1")
		self.end_btns['round'] = builder.get_object("end_btn_2")
		# self.end_btns['square'] = builder.get_object("end_btn_3")

		self.arrow_switch = builder.get_object("arrow_switch")

		for type_id in self.end_btns:
			self.end_btns[type_id].connect('clicked', self.on_end_changed)

		# Default values
		self.selected_shape_label = _("Round") # FIXME
		self.selected_curv_label = _("Straight") # FIXME
		self.selected_end_id = cairo.LineCap.ROUND
		self.wait_points = (-1.0, -1.0, -1.0, -1.0)

	def on_end_changed(self, b):
		self.selected_shape_label = b.get_label()
		self.active_end()

	def active_end(self):
		for end_id in self.end_btns:
			if self.end_btns[end_id].get_active():
				if end_id == 'none':
					self.selected_end_id = cairo.LineCap.BUTT
				elif end_id == 'round':
					self.selected_end_id = cairo.LineCap.ROUND
				elif end_id == 'square':
					self.selected_end_id = cairo.LineCap.SQUARE
				return self.selected_end_id
		return cairo.LineCap.ROUND

	def active_type(self):
		for type_id in self.type_btns:
			if self.type_btns[type_id].get_active():
				return type_id
		return 'line'

	def on_type_changed(self, b):
		self.selected_curv_label = b.get_label()
		self.wait_points = (-1.0, -1.0, -1.0, -1.0)

	def get_options_widget(self):
		return self.options_box

	def get_options_label(self):
		return self.selected_curv_label + ' - ' + self.selected_shape_label

	def give_back_control(self):
		self.wait_points = (-1.0, -1.0, -1.0, -1.0)
		self.x_press = 0.0
		self.y_press = 0.0

	def on_key_on_area(self, area, event, surface):
		pass

	def on_motion_on_area(self, area, event, surface):
		self.window.pre_modification()
		w_context = cairo.Context(self.window._surface)
		w_context.set_source_rgba(self.wanted_color.red, self.wanted_color.green, \
			self.wanted_color.blue, self.wanted_color.alpha)

		if self.active_type() == 'line':
			w_context.set_line_cap(self.selected_end_id)
			w_context.set_line_width(self.tool_width)
			w_context.move_to(self.x_press, self.y_press)
			w_context.line_to(event.x, event.y)
			w_context.stroke()

		elif self.active_type() == 'arc':
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

		self.window.drawing_area.queue_draw()

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color):
		print("press")
		self.window_can_take_back_control = False
		self.x_press = event.x
		self.y_press = event.y
		self.tool_width = tool_width
		if event.button == 1:
			self.wanted_color = left_color
		if event.button == 3:
			self.wanted_color = right_color

	def on_release_on_area(self, area, event, surface):
		if self.active_type() == 'line':
			self.window.pre_modification()
			w_context = cairo.Context(self.window._surface)
			w_context.set_source_rgba(self.wanted_color.red, self.wanted_color.green, \
				self.wanted_color.blue, self.wanted_color.alpha)

			w_context.set_line_cap(self.selected_end_id)
			w_context.set_line_width(self.tool_width)
			w_context.move_to(self.x_press, self.y_press)
			w_context.line_to(event.x, event.y)
			w_context.stroke()

			self.window_can_take_back_control = True

		elif self.active_type() == 'arc':
			if self.wait_points == (-1.0, -1.0, -1.0, -1.0):
				self.wait_points = (self.x_press, self.y_press, event.x, event.y)
			else:
				self.window.pre_modification()
				w_context = cairo.Context(self.window._surface)
				w_context.set_source_rgba(self.wanted_color.red, self.wanted_color.green, \
					self.wanted_color.blue, self.wanted_color.alpha)

				w_context.move_to(self.wait_points[0], self.wait_points[1])
				w_context.set_line_width(self.tool_width)
				w_context.set_line_cap(self.selected_end_id)
				w_context.curve_to(self.wait_points[2], self.wait_points[3], self.x_press, self.y_press, event.x, event.y)
				w_context.stroke()
				self.wait_points = (-1.0, -1.0, -1.0, -1.0)

				self.window_can_take_back_control = True

		if self.arrow_switch.get_active():
			print("arrow") # TODO

		self.x_press = 0.0
		self.y_press = 0.0
