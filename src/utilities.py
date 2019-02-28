# utilities.py TODO

from gi.repository import Gtk, Gdk, GdkPixbuf
import cairo, math

from .message_dialog import DrawingMessageDialog

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

def utilities_get_magic_path(surface, x, y, window, coef):
# TODO idée :
# le délire ce serait de commencer un path petit, puis de l'étendre avec
# cairo.Context.clip_extents() jusqu'à ce qu'on soit à fond.
# À partir de là on fait cairo.Context.paint()

	# Cairo doesn't provide methods for what we want to do. I will have to
	# define myself how to decide what should be filled.
	# The heuristic here is that we create a hull containing the area of
	# color we want to paint. We don't care about "enclaves" of other colors.
	cairo_context = cairo.Context(surface)
	old_color = utilities_get_rgb_for_xy(surface, x, y)

	while (utilities_get_rgb_for_xy(surface, x, y) == old_color) and y > 0:
		y = y - 1
	y = y + 1 # sinon ça crashe ?
	cairo_context.move_to(x, y)

	(first_x, first_y) = (x, y)

	print(str(x) + ' ' + str(y))

	# 0 1 2
	# 7   3
	# 6 5 4

	direction = 5
	should_stop = False
	i = 0

	x_shift = [-1 * coef, 0, coef, coef, coef, 0, -1 * coef, -1 * coef]
	y_shift = [-1 * coef, -1 * coef, -1 * coef, 0, coef, coef, coef, 0]

	while (not should_stop and i < 50000):
		new_x = -10
		new_y = -10
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
		if (new_x != -10):
			cairo_context.line_to(x, y)
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
			if result == 2: # Continue
				dialog.destroy()
			else: # Cancel
				dialog.destroy()
				return

	cairo_context.close_path()
	# print('i: ' + str(i))
	return cairo_context.copy_path()

def launch_infinite_loop_dialog(window):
	dialog = DrawingMessageDialog(window)
	dialog.set_actions([_("Cancel"), _("Continue")])
	dialog.add_string( _("""The area seems poorly delimited, or is very complex.
This algorithm may not be able to manage the wanted area.

Do you want to abort the operation, or to let the tool struggle ?""") )
	dialog.show_all()
	return dialog

def utilities_add_arrow_triangle(cairo_context, x_release, y_release, x_press, y_press, line_width):
	cairo_context.new_path()
	cairo_context.set_line_width(line_width)
	cairo_context.set_dash([1, 0])
	cairo_context.move_to(x_release, y_release)
	x_length = max(x_press, x_release) - min(x_press, x_release)
	y_length = max(y_press, y_release) - min(y_press, y_release)
	line_length = math.sqrt( (x_length)**2 + (y_length)**2 )
	arrow_width = math.log(line_length)
	if (x_press - x_release) != 0:
		delta = (y_press - y_release) / (x_press - x_release)
	else:
		delta = 1.0

	x_backpoint = (x_press + x_release)/2
	y_backpoint = (y_press + y_release)/2
	i = 0
	while i < arrow_width:
		i = i + 2
		x_backpoint = (x_backpoint + x_release)/2
		y_backpoint = (y_backpoint + y_release)/2

	if delta < -1.5 or delta > 1.0:
		cairo_context.line_to(x_backpoint-arrow_width, y_backpoint)
		cairo_context.line_to(x_backpoint+arrow_width, y_backpoint)
	elif delta > -0.5 and delta <= 1.0:
		cairo_context.line_to(x_backpoint, y_backpoint-arrow_width)
		cairo_context.line_to(x_backpoint, y_backpoint+arrow_width)
	else:
		cairo_context.line_to(x_backpoint-arrow_width, y_backpoint-arrow_width)
		cairo_context.line_to(x_backpoint+arrow_width, y_backpoint+arrow_width)

	cairo_context.close_path()
	cairo_context.fill_preserve()
	cairo_context.stroke()

def utilities_generic_shape_tool_operation(cairo_context, operation):
	cairo_context.set_operator(operation['operator'])
	cairo_context.set_line_width(operation['line_width'])
	cairo_context.set_line_join(operation['line_join'])
	rgba_main = operation['rgba_main']
	rgba_secd = operation['rgba_secd']
	cairo_context.append_path(operation['path'])
	filling = operation['filling']
	if filling == 'secondary':
		cairo_context.set_source_rgba(rgba_secd.red, rgba_secd.green, rgba_secd.blue, rgba_secd.alpha)
		cairo_context.fill_preserve()
		cairo_context.set_source_rgba(rgba_main.red, rgba_main.green, rgba_main.blue, rgba_main.alpha)
		cairo_context.stroke()
	elif filling == 'filled':
		cairo_context.set_source_rgba(rgba_main.red, rgba_main.green, rgba_main.blue, rgba_main.alpha)
		cairo_context.fill()
	else:
		cairo_context.set_source_rgba(rgba_main.red, rgba_main.green, rgba_main.blue, rgba_main.alpha)
		cairo_context.stroke()

