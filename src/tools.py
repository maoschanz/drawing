# methods that i don't want to implement in each tool

from gi.repository import Gtk, Gdk

def build_row(tool_object):
	tool_object.row = Gtk.RadioButton(draw_indicator=False)
	box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, margin=2, spacing=8)
	image = Gtk.Image().new_from_icon_name(tool_object.icon_name, Gtk.IconSize.BUTTON)
	box.add(image)
	tool_object.label_widget = Gtk.Label(label=tool_object.label)
	box.add(tool_object.label_widget)
	tool_object.row.add(box)

def get_rgb_for_xy(surface, x, y):
	# Guard clause: we can't perform color picking outside of the surface
	if x < 0 or x > surface.get_width() or y < 0 or y > surface.get_height():
		return [-1,-1,-1]
	screenshot = Gdk.pixbuf_get_from_surface(surface, float(x), float(y), 1, 1)
	rgb_vals = screenshot.get_pixels()
	return rgb_vals # array de 3 valeurs, de 0 à 255
