# pencil.py

from gi.repository import Gtk, Gdk, Gio, GLib
import cairo

from .tools import ToolTemplate

class ToolPencil(ToolTemplate):
	__gtype_name__ = 'ToolPencil'

	use_size = True

	def __init__(self, window, **kwargs):
		super().__init__('pencil', _("Pencil"), 'document-edit-symbolic', window)
		self.past_x = -1.0
		self.past_y = -1.0
		self._path = None
		self.main_color = None

		# Building the widget containing options
		builder = Gtk.Builder.new_from_resource("/com/github/maoschanz/Drawing/tools/ui/pencil.ui")
		self.options_box = builder.get_object('options-menu')
		self.dash_switch = builder.get_object("dash_switch")
		radio_btn_1 = builder.get_object('radio_btn_1')
		radio_btn_2 = builder.get_object('radio_btn_2')
		radio_btn_3 = builder.get_object('radio_btn_3')
		radio_btn_1.connect('clicked', self.on_option_changed, cairo.LineCap.ROUND)
		radio_btn_2.connect('clicked', self.on_option_changed, cairo.LineCap.BUTT)
		radio_btn_3.connect('clicked', self.on_option_changed, cairo.LineCap.SQUARE)
		self.selected_shape_label = _("Round")
		self.selected_shape_id = cairo.LineCap.ROUND

		# TODO
		model = builder.get_object('options-menu-beta')
		self.options_box2 = Gtk.Popover.new_from_model(window.options_btn, model)
		self.add_tool_action_enum('pencil_shape', 'round', self.osef)
		self.add_tool_action_boolean('pencil_dashes', False, self.osef)

	def osef(self, *args):
		pass

	def on_option_changed(self, *args):
		self.selected_shape_label = args[0].get_label()
		self.selected_shape_id = args[1]

	def get_options_widget(self):
		return self.options_box
		# return self.options_box2

	def get_options_label(self):
		return self.selected_shape_label

	def on_motion_on_area(self, area, event, surface):
		self.restore_pixbuf()
		w_context = cairo.Context(self.window.get_surface())
		w_context.set_line_cap(self.selected_shape_id)
		w_context.set_line_width(self.tool_width)
		w_context.set_source_rgba(self.main_color.red, self.main_color.green, \
				self.main_color.blue, self.main_color.alpha)
		if self.dash_switch.get_active():
			w_context.set_dash([2*self.tool_width, 2*self.tool_width])

		if self.past_x == -1.0:
			(self.past_x, self.past_y) = (self.x_press, self.y_press)
			w_context.move_to(self.x_press, self.y_press)
			self._path = w_context.copy_path()
		else:
			w_context.append_path(self._path)

		w_context.line_to(event.x, event.y)
		w_context.stroke_preserve() # draw the line without closing the path
		self._path = w_context.copy_path()
		self.non_destructive_show_modif()
		self.past_x = event.x
		self.past_y = event.y

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color):
		self.x_press = event.x
		self.y_press = event.y
		self.tool_width = tool_width
		if event.button == 3:
			self.main_color = right_color
		else:
			self.main_color = left_color

	def on_release_on_area(self, area, event, surface):
		self.past_x = -1.0
		self.past_y = -1.0
		self.apply_to_pixbuf()

