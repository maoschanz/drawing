# tools.py
#
# Super-class implemented and extended by all tools.

from gi.repository import Gtk, Gdk
import cairo

class ToolTemplate():
	__gtype_name__ = 'ToolTemplate'

	def __init__(self, tool_id, label, icon_name, window, is_hidden, **kwargs):
		self.id = tool_id
		self.label = label
		self.icon_name = icon_name
		self.is_hidden = is_hidden
		self.tool_width = 10
		self.selection_is_active = False
		self.use_size = False
		self.has_ongoing_operation = False
		self.build_row()
		self.window = window

	# Actions

	def add_tool_action_simple(self, action_name, callback):
		"""Convenient wrapper method adding a stateless action to the window. It
		will be named 'action_name' (string) and activating the action will
		trigger the method 'callback'."""
		self.window.add_action_simple(action_name, callback)

	def add_tool_action_boolean(self, action_name, default):
		self.window.options_manager.add_tool_option_boolean(action_name, default)

	def add_tool_action_enum(self, action_name, default):
		self.window.options_manager.add_tool_option_enum(action_name, default)

	def get_option_value(self, action_name):
		return self.window.options_manager.get_value(action_name)

	def set_action_sensitivity(self, action_name, state):
		self.window.lookup_action(action_name).set_enabled(state)

	def update_actions_state(self):
		pass

	# UI

	def show_panel(self, visibility):
		if self.implements_panel:
			self.window.bottom_panel.set_visible(not visibility)
			self.bottom_panel.set_visible(visibility)
		else:
			self.window.bottom_panel.set_visible(True)

	def add_item_to_menu(self, tools_menu):
		tools_menu.append(self.label, 'win.active_tool::' + self.id)

	def get_options_model(self):
		return None

	def get_options_widget(self):
		return None

	def get_edition_status(self):
		return self.label

	def get_options_label(self):
		return _("No options")

	def build_row(self):
		self.row = Gtk.RadioButton(draw_indicator=False, tooltip_text=self.label)
		self.row.set_detailed_action_name('win.active_tool::' + self.id)
		image = Gtk.Image().new_from_icon_name(self.icon_name, Gtk.IconSize.BUTTON)
		self.label_widget = Gtk.Label(label=self.label)
		box = Gtk.Box(
			orientation=Gtk.Orientation.HORIZONTAL,
			spacing=8,
			margin=2
		)
		box.add(image)
		box.add(self.label_widget)
		self.row.add(box)
		if not self.is_hidden:
			self.row.show_all()

	def build_selection_bar_btn(self):
		btn = Gtk.Button.new_from_icon_name(self.icon_name, Gtk.IconSize.BUTTON)
		btn.set_tooltip_text(self.label)
		btn.set_detailed_action_name('win.selection_' + self.id)
		btn.show_all()
		return btn

	def adapt_to_window_size(self):
		pass

	# Activation or not

	def on_tool_selected(self):
		pass

	def on_tool_unselected(self):
		pass

	def cancel_ongoing_operation(self):
		return self.give_back_control()

	def give_back_control(self):
		self.restore_pixbuf()
		self.non_destructive_show_modif()
		return False

	# History

	def do_tool_operation(self, operation):
		pass

	def apply_operation(self, operation):
		self.do_tool_operation(operation)
		self.non_destructive_show_modif()
		self.apply_to_pixbuf()
		self.get_image().add_operation_to_history(operation)

	# Miscellaneous

	def get_image(self):
		return self.window.get_active_image()

	def get_surface(self):
		return self.get_image().get_surface()

	def get_main_pixbuf(self):
		return self.get_image().get_main_pixbuf()

	def get_selection_pixbuf(self):
		return self.get_image().get_selection_pixbuf()

	def non_destructive_show_modif(self):
		self.get_image().queue_draw()

	def restore_pixbuf(self):
		self.get_image().use_stable_pixbuf()

	def apply_to_pixbuf(self):
		self.get_image().on_tool_finished()

	def on_motion_on_area(self, area, event, surface, event_x, event_y):
		pass

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color, event_x, event_y):
		pass

	def on_release_on_area(self, area, event, surface, event_x, event_y):
		pass

	def on_apply(self):
		pass

	def finish_temp_pixbuf_tool_operation(self, is_selection):
		cairo_context = cairo.Context(self.get_surface())
		if is_selection:
			cairo_context.set_source_surface(self.get_surface(), 0, 0)
			cairo_context.paint()
			self.get_image().delete_former_selection()
			Gdk.cairo_set_source_pixbuf(cairo_context, \
				self.get_image().get_temp_pixbuf(), \
				self.get_image().selection_x, \
				self.get_image().selection_y)
			cairo_context.paint()
		else:
			cairo_context.set_operator(cairo.Operator.CLEAR)
			cairo_context.paint()
			cairo_context.set_operator(cairo.Operator.OVER)
			Gdk.cairo_set_source_pixbuf(cairo_context, \
				self.get_image().get_temp_pixbuf(), \
				-1 * self.get_image().scroll_x, -1 * self.get_image().scroll_y)
			cairo_context.paint()
		self.non_destructive_show_modif()
