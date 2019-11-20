# utilities.py

import cairo, math
from gi.repository import Gtk, Gdk, GdkPixbuf
from .message_dialog import DrawingMessageDialog

################################################################################

def utilities_save_pixbuf_to(pixbuf, fpath):
	"""Save pixbuf to a given path, with the file format corresponding to the
	end of the file name. Format with no support for alpha channel will be
	modified so transparent pixels get replaced by white."""
	# Build a short string which will be recognized as a file format by the
	# GdkPixbuf.Pixbuf.savev method
	file_format = fpath.split('.')[-1]
	if file_format in ['jpeg', 'jpg', 'jpe']:
		file_format = 'jpeg'
	elif file_format not in ['jpeg', 'jpg', 'jpe', 'png', 'tiff', 'ico', 'bmp']:
		file_format = 'png'
	# Handle formats with no alpha channel
	if file_format not in ['png']:
		width = pixbuf.get_width()
		height = pixbuf.get_height()
		# TODO ask the user if they want something else than white?
		pattern_color1 = _rgb_as_hexadecimal_int(255, 255, 255)
		pattern_color2 = _rgb_as_hexadecimal_int(255, 255, 255)
		pixbuf = pixbuf.composite_color_simple(width, height, \
		                                      GdkPixbuf.InterpType.TILES, 255, \
		                                      8, pattern_color1, pattern_color2)
	# Actually save the pixbuf to the given file path
	pixbuf.savev(fpath, file_format, [None], [])

def _rgb_as_hexadecimal_int(r, g, b):
	"""The method GdkPixbuf.Pixbuf.composite_color_simple wants an hexadecimal
	integer whose format is 0xaarrggbb so here are ugly binary operators."""
	return (r << 16) + (g << 8) + b

################################################################################

def utilities_add_filechooser_filters(dialog):
	"""Add file filters for images to file chooser dialogs."""
	allPictures = Gtk.FileFilter()
	allPictures.set_name(_("All pictures"))
	allPictures.add_mime_type('image/png')
	allPictures.add_mime_type('image/jpeg')
	allPictures.add_mime_type('image/bmp')

	pngPictures = Gtk.FileFilter()
	pngPictures.set_name(_("PNG images"))
	pngPictures.add_mime_type('image/png')

	jpegPictures = Gtk.FileFilter()
	jpegPictures.set_name(_("JPEG images"))
	jpegPictures.add_mime_type('image/jpeg')

	bmpPictures = Gtk.FileFilter()
	bmpPictures.set_name(_("BMP images"))
	bmpPictures.add_mime_type('image/bmp')

	dialog.add_filter(allPictures)
	dialog.add_filter(pngPictures)
	dialog.add_filter(jpegPictures)
	dialog.add_filter(bmpPictures)

################################################################################

def utilities_get_rgb_for_xy(surface, x, y):
	# Guard clause: we can't perform color picking outside of the surface
	if x < 0 or x > surface.get_width() or y < 0 or y > surface.get_height():
		return [-1,-1,-1]
	screenshot = Gdk.pixbuf_get_from_surface(surface, float(x), float(y), 1, 1)
	rgb_vals = screenshot.get_pixels()
	return rgb_vals # array de 3 valeurs, de 0 à 255

def utilities_get_rgba_name(red, green, blue, alpha):
	"""To improve accessibility, it is useful to display the name of the colors.
	Sadly, it's a mess to implement, and it's quite approximative."""
	color_string = ""
	alpha_string = ""
	if alpha == 0.0:
		return _("Transparent")
	elif alpha < 1.0:
		alpha_string = ' - ' + _("%s%% transparent") % int(100 - alpha * 100)

	total = red + green + blue
	orange_coef = 0.0
	lumin = total/3.0
	# print(lumin)
	if green != 0:
		orange_coef = (red/green) * lumin

	if total != 0:
		rgb_percents = [red/total, green/total, blue/total]
	else:
		rgb_percents = [0.333, 0.333, 0.333]
	# print(rgb_percents)

	grey_coef_r = rgb_percents[0] * lumin / 3
	grey_coef_g = rgb_percents[1] * lumin / 3
	grey_coef_b = rgb_percents[2] * lumin / 3
	is_grey = abs(grey_coef_r - grey_coef_g) < 0.01
	is_grey = is_grey and abs(grey_coef_g - grey_coef_b) < 0.01
	is_grey = is_grey and abs(grey_coef_b - grey_coef_r) < 0.01

	if is_grey:
		if lumin > 0.9:
			color_string = _("White")
		elif lumin < 0.1:
			color_string = _("Black")
		else:
			color_string = _("Grey")
			print('gris correct')

	elif rgb_percents[0] > 0.5 and rgb_percents[1] > 0.2 and rgb_percents[1] < 0.4:
		if orange_coef > 0.87:
			color_string = _("Orange")
		else:
			color_string = _("Brown")

	elif rgb_percents[0] > 0.4 and rgb_percents[1] < 0.3 and rgb_percents[2] < 0.3:
		if lumin < 0.7 and rgb_percents[0] < 0.7:
			color_string = _("Probably brown")
		else:
			color_string = _("Red")
	elif rgb_percents[1] > 0.4 and rgb_percents[0] < 0.4 and rgb_percents[2] < 0.4:
		color_string = _("Green")
	elif rgb_percents[2] > 0.4 and rgb_percents[0] < 0.3 and rgb_percents[1] < 0.4:
		color_string = _("Blue")

	elif rgb_percents[0] > 0.3 and rgb_percents[1] > 0.3 and rgb_percents[2] < 0.3:
		if rgb_percents[1] < 0.4:
			color_string = _("Probably brown")
		else:
			color_string = _("Yellow")
	elif rgb_percents[0] > 0.3 and rgb_percents[2] > 0.3 and rgb_percents[1] < 0.3:
		if lumin > 0.6 and rgb_percents[1] < 0.1:
			color_string = _("Magenta")
		else:
			color_string = _("Purple")
	elif rgb_percents[1] > 0.3 and rgb_percents[2] > 0.3 and rgb_percents[0] < 0.2:
		if lumin > 0.7:
			color_string = _("Cyan")
		else:
			color_string = _("Probably turquoise")

	else:
		color_string = _("Unknown color name")

	# print(color_string)
	return (color_string + alpha_string)

################################################################################

def utilities_show_overlay_on_context(cairo_context, cairo_path, has_dashes):
	"""Draw a blueish area on `cairo_context`, with or without dashes. This is
	mainly used for the selection."""
	if cairo_path is None:
		return
	cairo_context.new_path()
	cairo_context.set_line_width(1)
	if has_dashes:
		cairo_context.set_dash([3, 3])
	cairo_context.append_path(cairo_path)
	cairo_context.set_source_rgba(0.1, 0.1, 0.3, 0.2)
	cairo_context.fill_preserve()
	cairo_context.set_source_rgba(0.5, 0.5, 0.5, 0.5)
	cairo_context.stroke()

def utilities_get_magic_path(surface, x, y, window, coef):
	"""This method tries to build a path defining an area of the same color. It
	will mainly be used to paint this area, or to select it."""
	cairo_context = cairo.Context(surface)
	old_color = utilities_get_rgb_for_xy(surface, x, y)

	# Cairo doesn't provide methods for what we want to do. I will have to
	# define myself how to decide what should be filled.
	# The heuristic here is that we create a hull containing the area of
	# color we want to paint. We don't care about "enclaves" of other colors.
	while (utilities_get_rgb_for_xy(surface, x, y) == old_color) and y > 0:
		y = y - 1
	y = y + 1 # sinon ça crashe ?
	cairo_context.move_to(x, y)

	(first_x, first_y) = (x, y)

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
			future_x = x+x_shift[direction]
			future_y = y+y_shift[direction]
			if (utilities_get_rgb_for_xy(surface, future_x, future_y) == old_color) \
			and (future_x > 0) and (future_y > 0) \
			and (future_x < surface.get_width()) \
			and (future_y < surface.get_height()-2): # ???
				new_x = future_x
				new_y = future_y
				direction = (direction+1) % 8
			elif (x != new_x or y != new_y):
				x = new_x+x_shift[direction]
				y = new_y+y_shift[direction]
				end_circle = True
			j = j+1

		direction = (direction+4) % 8
		if (new_x != -10):
			cairo_context.line_to(x, y)

		if (i > 10) and (first_x-5 < x < first_x+5) and (first_y-5 < y < first_y+5):
			should_stop = True

		i = i + 1

		if i == 2000:
			dialog, continue_id = launch_infinite_loop_dialog(window)
			result = dialog.run()
			if result == continue_id: # Continue
				dialog.destroy()
			else: # Cancel
				dialog.destroy()
				return

	cairo_context.close_path()
	return cairo_context.copy_path()

def launch_infinite_loop_dialog(window):
	dialog = DrawingMessageDialog(window)
	cancel_id = dialog.set_action(_("Cancel"), None, False)
	continue_id = dialog.set_action(_("Continue"), None, True)
	dialog.add_string( _("""The area seems poorly delimited, or is very complex.
This algorithm may not be able to manage the wanted area.

Do you want to abort the operation, or to let the tool struggle ?""") )
	return dialog, continue_id

################################################################################

def utilities_add_arrow_triangle(cairo_context, x2, y2, x1, y1, line_width):
	cairo_context.new_path()
	cairo_context.set_line_width(line_width)
	cairo_context.set_dash([1, 0])
	cairo_context.move_to(x2, y2)
	x_length = max(x1, x2) - min(x1, x2)
	y_length = max(y1, y2) - min(y1, y2)
	line_length = math.sqrt( (x_length)**2 + (y_length)**2 )
	arrow_width = math.log(line_length)
	if (x1 - x2) != 0:
		delta = (y1 - y2) / (x1 - x2)
	else:
		delta = 1.0

	x_backpoint = (x1 + x2)/2
	y_backpoint = (y1 + y2)/2
	i = 0
	while i < arrow_width:
		i = i + 2
		x_backpoint = (x_backpoint + x2)/2
		y_backpoint = (y_backpoint + y2)/2

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

################################################################################

def utilities_add_unit_to_spinbtn(spinbutton, width_chars, unit):
	spinbutton.set_width_chars(width_chars + 3)
	if unit == 'px':
		_add_spinbutton_icon(spinbutton, 'unit-pixels-symbolic', _("pixels"))
	elif unit == '%':
		_add_spinbutton_icon(spinbutton, 'unit-percents-symbolic', _("percents"))

def _add_spinbutton_icon(spinbutton, icon, tooltip):
	p = Gtk.EntryIconPosition.SECONDARY
	spinbutton.set_icon_from_icon_name(p, icon)
	spinbutton.set_icon_tooltip_text(p, tooltip)
	spinbutton.set_icon_sensitive(p, False)

################################################################################

def utilities_smooth_path(cairo_context, cairo_path):
	"""Extrapolate a path made of straight lines into a path made of curves. New
	points are added according to the length of the line it replaces, the length
	of the previous one, and the length of the next one."""
	x1 = None
	y1 = None
	x2 = None
	y2 = None
	x3 = None
	y3 = None
	x4 = None
	y4 = None
	for pts in cairo_path:
		if pts[1] is ():
			continue
		x1, y1, x2, y2, x3, y3, x4, y4 = _next_arc(cairo_context, \
		                           x2, y2, x3, y3, x4, y4, pts[1][0], pts[1][1])
	_next_arc(cairo_context, x2, y2, x3, y3, x4, y4, None, None)
	# cairo_context.stroke()

def _next_point(x1, y1, x2, y2, dist):
	coef = 0.1
	dx = x2 - x1
	dy = y2 - y1
	angle = math.atan2(dy, dx)
	nx = x2 + math.cos(angle) * dist * coef
	ny = y2 + math.sin(angle) * dist * coef
	return nx, ny

def _next_arc(cairo_context, x1, y1, x2, y2, x3, y3, x4, y4):
	if x2 is None or x3 is None:
		# No drawing possible yet, just continue to the next point
		return x1, y1, x2, y2, x3, y3, x4, y4
	dist = math.sqrt( (x2 - x3) * (x2 - x3) + (y2 - y3) * (y2 - y3) )
	if x1 is None and x4 is None:
		cairo_context.move_to(x2, y2)
		cairo_context.line_to(x3, y3)
		return x1, y1, x2, y2, x3, y3, x4, y4
	elif x1 is None:
		nx1, ny1 = x2, y2
		nx2, ny2 = _next_point(x4, y4, x3, y3, dist)
	elif x4 is None:
		nx1, ny1 = _next_point(x1, y1, x2, y2, dist)
		nx2, ny2 = x3, y3
	else:
		nx1, ny1 = _next_point(x1, y1, x2, y2, dist)
		nx2, ny2 = _next_point(x4, y4, x3, y3, dist)
	cairo_context.curve_to(nx1, ny1, nx2, ny2, x3, y3)
	return x1, y1, x2, y2, x3, y3, x4, y4

################################################################################

