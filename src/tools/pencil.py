# pencil.py

from gi.repository import Gtk, Gdk, Gio
import cairo

from .tools import ToolTemplate

class ToolPencil(ToolTemplate):
	__gtype_name__ = 'ToolPencil'

	use_size = True

	def __init__(self, window, **kwargs):
		super().__init__('pencil', _("Pencil"), 'document-edit-symbolic', window)
		self.past_x = -1
		self.past_y = -1
		self.w_context = None

		# Building the widget containing options
		builder = Gtk.Builder.new_from_resource("/com/github/maoschanz/Drawing/tools/ui/pencil.ui")
		self.options_box = builder.get_object('options-menu')
		radio_btn_1 = builder.get_object('radio_btn_1')
		radio_btn_2 = builder.get_object('radio_btn_2')
		radio_btn_3 = builder.get_object('radio_btn_3')
		radio_btn_1.connect('clicked', self.on_option_changed, cairo.LineCap.ROUND)
		radio_btn_2.connect('clicked', self.on_option_changed, cairo.LineCap.BUTT)
		radio_btn_3.connect('clicked', self.on_option_changed, cairo.LineCap.SQUARE)
		self.selected_shape_label = _("Round")
		self.selected_shape_id = cairo.LineCap.ROUND

	def on_option_changed(self, *args):
		self.selected_shape_label = args[0].get_label()
		self.selected_shape_id = args[1]

	def get_options_widget(self):
		return self.options_box

	def get_options_label(self):
		return self.selected_shape_label

	def on_motion_on_area(self, area, event, surface):
		self.w_context.set_line_cap(self.selected_shape_id)
		self.w_context.set_line_width(self.tool_width)
		if (self.past_x > 0):
			self.w_context.move_to(self.past_x, self.past_y)
		self.w_context.line_to(event.x, event.y)
		self.past_x = event.x
		self.past_y = event.y
		self.w_context.stroke()

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color):
		self.window_can_take_back_control = False
		self.tool_width = tool_width
		self.w_context = cairo.Context(surface)
		if event.button == 1:
			self.w_context.set_source_rgba(left_color.red, left_color.green, left_color.blue, left_color.alpha)
		if event.button == 3:
			self.w_context.set_source_rgba(right_color.red, right_color.green, right_color.blue, right_color.alpha)

	def on_release_on_area(self, area, event, surface):
		self.past_x = -1
		self.past_y = -1
		self.window_can_take_back_control = True
