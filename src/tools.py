# methods that i don't want to implement in each tool

from gi.repository import Gtk, Gdk, Gio

class ToolTemplate():
	__gtype_name__ = 'ToolTemplate'

	use_size = False

	def __init__(self, tool_id, label, icon_name, window, **kwargs):
		self.id = tool_id
		self.label = label
		self.icon_name = icon_name
		self.tool_width = 10
		self.selection_is_active = False
		self.build_row()
		self.window = window

	# Actions

	def add_tool_action(self, action_name, callback):
		self.window.add_action_simple(action_name, callback)

	def add_tool_action_boolean(self, action_name, default, callback):
		self.window.add_action_boolean(action_name, default, callback)

	def add_tool_action_enum(self, action_name, default, callback):
		self.window.add_action_enum(action_name, default, callback)

	def set_action_sensitivity(self, action_name, state):
		self.window.lookup_action(action_name).set_enabled(state)

	def update_actions_state(self):
		pass

	# UI

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
		self.row = Gtk.RadioButton(draw_indicator=False)
		self.row.set_detailed_action_name('win.active_tool::' + self.id)
		image = Gtk.Image().new_from_icon_name(self.icon_name, Gtk.IconSize.BUTTON)
		self.label_widget = Gtk.Label(label=self.label)
		box = Gtk.Box(
			orientation=Gtk.Orientation.HORIZONTAL,
			margin=2,
			spacing=8,
			tooltip_text=self.label
		)
		box.add(image)
		box.add(self.label_widget)
		self.row.add(box)

	# Activation or not

	def on_tool_selected(self):
		pass

	def on_tool_unselected(self):
		pass

	def cancel_ongoing_operation(self):
		return self.give_back_control()

	def give_back_control(self):
		return False

	# History

	def do_tool_operation(self, operation):
		pass

	def apply_operation(self, operation):
		self.do_tool_operation(operation)
		self.non_destructive_show_modif()
		self.apply_to_pixbuf()
		self.window.add_operation_to_history(operation)

	# Drawing

	def non_destructive_show_modif(self):
		self.window.drawing_area.queue_draw()

	def restore_pixbuf(self):
		self.window.use_stable_pixbuf()

	def apply_to_pixbuf(self):
		self.window.on_tool_finished()

	def on_motion_on_area(self, area, event, surface, event_x, event_y):
		pass

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color, event_x, event_y):
		pass

	def on_release_on_area(self, area, event, surface, event_x, event_y):
		pass
