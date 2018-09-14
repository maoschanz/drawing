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
		self.options_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=10)

		self.options_box.add(Gtk.Label(label=_("Line type:")))
		curv_btn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		curv_btn_box.get_style_context().add_class('linked')

		self.type_btns['line'] = Gtk.RadioButton(draw_indicator=False, label=_("Straight"))
		self.type_btns['arc'] = Gtk.RadioButton(group=self.type_btns['line'], draw_indicator=False, label=_("Arc"))
		self.type_btns['arrow'] = Gtk.RadioButton(group=self.type_btns['line'], draw_indicator=False, label=_("Arrow"))

		for type_id in self.type_btns:
			self.type_btns[type_id].connect('clicked', self.on_type_changed)
			curv_btn_box.add(self.type_btns[type_id])

		self.options_box.add(curv_btn_box)

		self.options_box.add(Gtk.Label(label=_("Line end shape:")))
		end_btn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		end_btn_box.get_style_context().add_class('linked')

		self.end_btns['none'] = Gtk.RadioButton(draw_indicator=False, label=_("None"))
		self.end_btns['round'] = Gtk.RadioButton(group=self.end_btns['none'], draw_indicator=False, label=_("Round"))
		self.end_btns['square'] = Gtk.RadioButton(group=self.end_btns['none'], draw_indicator=False, label=_("Square"))

		for type_id in self.end_btns:
			self.end_btns[type_id].connect('clicked', self.on_end_changed)
			end_btn_box.add(self.end_btns[type_id])

		self.options_box.add(end_btn_box)

		# Default values
		self.type_btns['line'].set_active(True)
		self.end_btns['round'].set_active(True)
		self.selected_shape_label = _("Round")
		self.selected_curv_label = _("Straight")
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
		print("key")

	def on_motion_on_area(self, area, event, surface):
		pass

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color):
		print("press")
		self.window_can_take_back_control = False
		self.x_press = event.x
		self.y_press = event.y
		self.tool_width = tool_width
		self.left_color = left_color
		self.right_color = right_color

	def on_release_on_area(self, area, event, surface):

		w_context = cairo.Context(surface)
		if event.button == 1:
			w_context.set_source_rgba(self.left_color.red, self.left_color.green, \
				 self.left_color.blue, self.left_color.alpha)
		if event.button == 3:
			w_context.set_source_rgba(self.right_color.red, self.right_color.green, \
				self.right_color.blue, self.right_color.alpha)

		if self.active_type() == 'line':

			w_context.set_line_cap(self.selected_end_id)
			w_context.set_line_width(self.tool_width)
			w_context.move_to(self.x_press, self.y_press)
			w_context.line_to(event.x, event.y)
			w_context.stroke()

			self.window_can_take_back_control = True

		elif self.active_type() == 'arc':

			w_context.set_line_cap(self.selected_end_id)

			# FIXME si self.x_press, self.y_press est trop proche de event.x, event.y
			# il va falloir gérer autrement pour avoir un bézier à un point de contrôle
			# (sans le move_to donc, comme le prévoit la doc)

			if self.wait_points == (-1.0, -1.0, -1.0, -1.0):
				self.wait_points = (self.x_press, self.y_press, event.x, event.y)
			else:
				w_context.move_to(self.wait_points[0], self.wait_points[1])
				w_context.set_line_width(self.tool_width)
				w_context.curve_to(self.wait_points[2], self.wait_points[3], self.x_press, self.y_press, event.x, event.y)
				w_context.stroke()
				self.wait_points = (-1.0, -1.0, -1.0, -1.0)

				self.window_can_take_back_control = True

		elif sself.active_type() == 'arrow':

			print("arrow") # TODO
			self.window_can_take_back_control = True

		self.x_press = 0.0
		self.y_press = 0.0
