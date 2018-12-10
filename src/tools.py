# methods that i don't want to implement in each tool

from gi.repository import Gtk, Gdk, Gio

def get_rgb_for_xy(surface, x, y):
	# Guard clause: we can't perform color picking outside of the surface
	if x < 0 or x > surface.get_width() or y < 0 or y > surface.get_height():
		return [-1,-1,-1]
	screenshot = Gdk.pixbuf_get_from_surface(surface, float(x), float(y), 1, 1)
	rgb_vals = screenshot.get_pixels()
	return rgb_vals # array de 3 valeurs, de 0 à 255

#-------------------------------------------------------------------------------

class ToolTemplate():
	__gtype_name__ = 'ToolTemplate'

	id = 'template'
	icon_name = 'folder-templates-symbolic'
	label = "Not implemented"
	tool_width = 10
	use_size = False

	def __init__(self, tool_id, label, icon_name, window, **kwargs):
		self.id = tool_id
		self.label = label
		self.icon_name = icon_name
		self.build_row()
		self.window = window

	def add_item_to_menu(self, tools_menu):
		tools_menu.append(self.label, 'win.active_tool::' + self.id)

	def add_tool_action(self, action_name, callback):
		self.window.add_action_like_a_boss(action_name, callback)

	def non_destructive_show_modif(self):
		self.window.drawing_area.queue_draw()

	def restore_pixbuf(self):
		self.window._pixbuf_manager.use_stable_pixbuf()

	def apply_to_pixbuf(self):
		self.window._pixbuf_manager.on_tool_finished()

	def give_back_control(self):
		pass

	def get_options_widget(self):
		return None

	def get_options_label(self):
		return _("No options")

	def on_motion_on_area(self, area, event, surface):
		pass

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color):
		pass

	def on_release_on_area(self, area, event, surface):
		pass

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
