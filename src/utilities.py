# utilities.py TODO

from gi.repository import Gtk, Gdk, GdkPixbuf
import cairo

def utilities_get_rgb_for_xy(surface, x, y):
	# Guard clause: we can't perform color picking outside of the surface
	if x < 0 or x > surface.get_width() or y < 0 or y > surface.get_height():
		return [-1,-1,-1]
	screenshot = Gdk.pixbuf_get_from_surface(surface, float(x), float(y), 1, 1)
	rgb_vals = screenshot.get_pixels()
	return rgb_vals # array de 3 valeurs, de 0 à 255

def utilities_save_pixbuf_at(pixbuf, fn):
	file_format = fn.split('.')[-1]
	if file_format not in ['jpeg', 'jpg', 'jpe', 'png', 'tiff', 'ico', 'bmp']:
		file_format = 'png'
	pixbuf.savev(fn, file_format, [None], [])

def utilities_show_overlay_on_surface(surface, cairo_path, has_dashes):
	if cairo_path is None:
		return
	w_context = cairo.Context(surface)
	w_context.new_path()
	if has_dashes:
		w_context.set_dash([3, 3])
	w_context.append_path(cairo_path)
	w_context.clip_preserve()
	w_context.set_source_rgba(0.1, 0.1, 0.3, 0.2)
	w_context.paint()
	w_context.set_source_rgba(0.5, 0.5, 0.5, 0.5)
	w_context.stroke()
