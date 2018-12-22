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

		self.selected_shape_label = _("Round")
		self.selected_shape_id = cairo.LineCap.ROUND
		self.use_dashes = False
		self.is_smooth = True

		# Building the widget containing options
		builder = Gtk.Builder.new_from_resource("/com/github/maoschanz/Drawing/tools/ui/pencil.ui")
		model = builder.get_object('options-menu')
		self.options_menu = Gtk.Popover.new_from_model(window.options_btn, model)
		self.add_tool_action_enum('pencil_shape', 'round', self.on_change_active_shape)
		self.add_tool_action_boolean('pencil_dashes', False, self.set_dashes_state)
		self.add_tool_action_boolean('pencil_smooth', False, self.set_smooth_state)

	def set_smooth_state(self, *args):
		if not args[0].get_state():
			self.is_smooth = True
			args[0].set_state(GLib.Variant.new_boolean(True))
		else:
			self.is_smooth = False
			args[0].set_state(GLib.Variant.new_boolean(False))

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
			self.selected_shape_id = cairo.LineCap.BUTT
			self.selected_shape_label = _("Thin")
		elif state_as_string == 'square':
			self.selected_shape_id = cairo.LineCap.SQUARE
			self.selected_shape_label = _("Square")
		else:
			self.selected_shape_id = cairo.LineCap.ROUND
			self.selected_shape_label = _("Round")

	def get_options_widget(self):
		return self.options_menu

	def get_options_label(self):
		return self.selected_shape_label

	def on_motion_on_area(self, area, event, surface):
		if self.is_smooth:
			self.restore_pixbuf()
		w_context = cairo.Context(self.window.get_surface())
		w_context.set_line_cap(self.selected_shape_id)
		w_context.set_line_width(self.tool_width)
		w_context.set_source_rgba(self.main_color.red, self.main_color.green, \
				self.main_color.blue, self.main_color.alpha)
		if self.use_dashes:
			w_context.set_dash([2*self.tool_width, 2*self.tool_width])

		if not self.is_smooth:
			if self.past_x == -1.0:
				(self.past_x, self.past_y) = (self.x_press, self.y_press)
			w_context.move_to(self.past_x, self.past_y)
			w_context.line_to(event.x, event.y)
			w_context.stroke()
		else:
			w_context = cairo.Context(self.window.get_surface())
			w_context.set_line_cap(self.selected_shape_id)
			w_context.set_line_width(self.tool_width)
			w_context.set_source_rgba(self.main_color.red, self.main_color.green, \
					self.main_color.blue, self.main_color.alpha)
			if self.use_dashes:
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

