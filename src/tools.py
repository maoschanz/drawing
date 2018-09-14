# methods that i don't want to implement in each tool

from gi.repository import Gtk, Gdk

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
	label = _("To do")
	use_options = False
	window_can_take_back_control = True
	tool_width = 10
	use_size = False
	set_clip = False

	def __init__(self, window, **kwargs):
		self.build_row()
		self.window = window

	def give_back_control(self):
		pass

	def on_key_on_area(self, area, event, surface):
		pass

	def on_motion_on_area(self, area, event, surface):
		pass

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color):
		pass

	def on_release_on_area(self, area, event, surface):
		pass

	def build_row(self):
		self.row = Gtk.RadioButton(draw_indicator=False)
		box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, margin=2, spacing=8)
		image = Gtk.Image().new_from_icon_name(self.icon_name, Gtk.IconSize.BUTTON)
		box.add(image)
		self.label_widget = Gtk.Label(label=self.label)
		box.add(self.label_widget)
		self.row.add(box)
