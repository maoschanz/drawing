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
	if file_format in ['jpeg', 'jpg', 'jpe']:
		file_format = 'jpeg'
	elif file_format not in ['jpeg', 'jpg', 'jpe', 'png', 'tiff', 'ico', 'bmp']:
		file_format = 'png'
	pixbuf.savev(fn, file_format, [None], [])

def utilities_show_overlay_on_context(cairo_context, cairo_path, has_dashes):
	if cairo_path is None:
		return
	cairo_context.new_path()
	if has_dashes:
		cairo_context.set_dash([3, 3])
	cairo_context.append_path(cairo_path)
	cairo_context.clip_preserve()
	cairo_context.set_source_rgba(0.1, 0.1, 0.3, 0.2)
	cairo_context.paint()
	cairo_context.set_source_rgba(0.5, 0.5, 0.5, 0.5)
	cairo_context.stroke()

def utilities_get_magic_path(surface, x, y, window):
# TODO idée :
# le délire ce serait de commencer un path petit, puis de l'étendre avec
# cairo.Context.clip_extents() jusqu'à ce qu'on soit à fond.
# À partir de là on fait cairo.Context.paint()

# TODO meilleure idée : on fait un path approximatif, puis on utilise GdkPixbuf
# et sa méthode qui remplace un rgb par un alpha (??)

	# Cairo doesn't provide methods for what we want to do. I will have to
	# define myself how to decide what should be filled.
	# The heuristic here is that we create a hull containing the area of
	# color we want to paint. We don't care about "enclaves" of other colors.
	w_context = cairo.Context(surface)
	old_color = utilities_get_rgb_for_xy(surface, x, y)

	while (utilities_get_rgb_for_xy(surface, x, y) == old_color) and y > 0:
		y = y - 1
	y = y + 1 # sinon ça crashe ?
	w_context.move_to(x, y)

	(first_x, first_y) = (x, y)

	print(str(x) + ' ' + str(y))

	# 0 1 2
	# 7   3
	# 6 5 4

	direction = 5
	should_stop = False
	i = 0

	x_shift = [-1, 0, 1, 1, 1, 0, -1, -1]
	y_shift = [-1, -1, -1, 0, 1, 1, 1, 0]

	while (not should_stop and i < 50000):
		new_x = -2
		new_y = -2
		end_circle = False

		j = 0
		while (not end_circle) or (j < 8):
			if (utilities_get_rgb_for_xy(surface, x+x_shift[direction], y+y_shift[direction]) == old_color) \
			and (x+x_shift[direction] > 0) \
			and (y+y_shift[direction] > 0) \
			and (x+x_shift[direction] < surface.get_width()) \
			and (y+y_shift[direction] < surface.get_height()-2): # ???
				new_x = x+x_shift[direction]
				new_y = y+y_shift[direction]
				direction = (direction+1) % 8
			elif (x != new_x or y != new_y):
				x = new_x+x_shift[direction]
				y = new_y+y_shift[direction]
				end_circle = True
			else:
				print('cas emmerdant')
			j = j+1

		direction = (direction+4) % 8
		# print('direction:')
		# print(direction)
		if (new_x != -2):
			w_context.line_to(x, y)
		# else:
		#	 print('TENTATIVE ABUSIVE D\'AJOUT')
		#	 should_stop = True

		if (i > 10) and (first_x-5 < x < first_x+5) and (first_y-5 < y < first_y+5):
			should_stop = True

		i = i + 1
		# print('----------')

		if i == 2000:
			dialog = launch_infinite_loop_dialog(window)
			result = dialog.run()
			if result == -10:
				dialog.destroy()
			else:
				dialog.destroy()
				return

	w_context.close_path()
	# print('i: ' + str(i))
	return w_context.copy_path()

def launch_infinite_loop_dialog(window):
	dialog = Gtk.Dialog(use_header_bar=True, modal=True, title=_("Warning"), transient_for=window)
	dialog.add_button(_("Continue"), Gtk.ResponseType.APPLY)
	dialog.add_button(_("Abort"), Gtk.ResponseType.CANCEL)
	dialog.get_content_area().add(Gtk.Label(label=_( \
"""The area seems poorly delimited, or is very complex.
This algorithm is not may not be able to manage the wanted area.

Do you want to abort the operation, or to let the tool struggle ?""" \
	), margin=10))
	dialog.show_all()
	return dialog

