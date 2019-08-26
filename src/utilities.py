# utilities.py

from gi.repository import Gtk, Gdk, GdkPixbuf
import cairo, math, threading

from .message_dialog import DrawingMessageDialog

################################################################################

def utilities_save_pixbuf_at(pixbuf, fn):
	file_format = fn.split('.')[-1]
	if file_format in ['jpeg', 'jpg', 'jpe']:
		file_format = 'jpeg'
	elif file_format not in ['jpeg', 'jpg', 'jpe', 'png', 'tiff', 'ico', 'bmp']:
		file_format = 'png'
	pixbuf.savev(fn, file_format, [None], [])

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

################################################################################

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
	# print(str(x) + ' ' + str(y))

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
			# else:
			# 	print('cas emmerdant')
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
			dialog, continue_id = launch_infinite_loop_dialog(window)
			result = dialog.run()
			if result == continue_id: # Continue
				dialog.destroy()
			else: # Cancel
				dialog.destroy()
				return

	cairo_context.close_path()
	# print('i: ' + str(i))
	return cairo_context.copy_path()

def launch_infinite_loop_dialog(window):
	dialog = DrawingMessageDialog(window)
	cancel_id = dialog.set_action(_("Cancel"), None, False)
	continue_id = dialog.set_action(_("Continue"), None, True)
	dialog.add_string( _("""The area seems poorly delimited, or is very complex.
This algorithm may not be able to manage the wanted area.

Do you want to abort the operation, or to let the tool struggle ?""") )
	return dialog, continue_id

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

def utilities_add_px_to_spinbutton(spinbutton, width_chars, unit):
	spinbutton.set_width_chars(width_chars + 3)
	if unit == 'px':
		spinbutton.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, 'unit-pixels-symbolic')
		spinbutton.set_icon_tooltip_text(Gtk.EntryIconPosition.SECONDARY, _("pixels"))
	spinbutton.set_icon_sensitive(Gtk.EntryIconPosition.SECONDARY, False)

################################################################################

def utilities_smooth_path(cairo_context, cairo_path):
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

from datetime import datetime
ALGO = 2

def utilities_fast_blur(surface, radius, iterations):
	radius = int(radius)
	if radius < 1 or iterations < 1:
		return
	w = surface.get_width()
	h = surface.get_height()
	channels = 4 # XXX ou 3 dans le cas de RGB256 ???
	if radius > w - 1 or radius > h - 1:
		return

	# this code a modified version of this https://github.com/elementary/granite/blob/14e3aaa216b61f7e63762214c0b36ee97fa7c52b/lib/Drawing/BufferSurface.vala#L230
	# main differences (aside of the language) is the poor attempt to use
	# multithreading (i'm quite sure the access to buffers for example are
	# not safe at all)
	original = cairo.ImageSurface(cairo.Format.ARGB32, w, h)
	cairo_context = cairo.Context(original)
	# cairo_context.set_operator(cairo.Operator.SOURCE)
	cairo_context.set_source_surface(surface, 0, 0)
	cairo_context.paint()
	original.flush()
	pixels = original.get_data()

	buffer = [None] * (w * h * channels)
	vmin = [None] * max(w, h)
	vmax = [None] * max(w, h)
	div = 2 * radius + 1
	dv = [None] * (256 * div)
	for i in range(0, len(dv)):
		dv[i] = int(i / div)

	while iterations > 0:
		iterations = iterations - 1

		print('ALGO:', ALGO)
		print(w, h)
		print('begin blur', datetime.now())
		if ALGO == 1:
			# 1 thread
			# 42.9 à 46.6 = 3.7
			# 41.3 à 45.3 = 4.0
			# 18.9 à 22.4 = 3.5
			_fast_blur_1st_phase1(w, h, channels, radius, pixels, buffer, vmin, vmax, dv)
			print('new phase…', datetime.now())
			_fast_blur_2nd_phase1(w, h, channels, radius, pixels, buffer, vmin, vmax, dv)
		elif ALGO == 2:
			# 4+4 threads
			# 2.9 à 7.5 = 4.6
			# 49.8 à 54.4 = 4.6
			# 56.0 à 0.5 = 4.5
			_fast_blur_1st_phase2(w, h, channels, radius, pixels, buffer, vmin, vmax, dv)
			print('new phase…', datetime.now())
			_fast_blur_2nd_phase2(w, h, channels, radius, pixels, buffer, vmin, vmax, dv)
		elif ALGO == 0:
			# h+w threads
			# 44.7 à 49.4 = 4.7
			# 41.2 à 45.5 = 4.3
			# 41.8 à 46.2 = 4.4
			_fast_blur_1st_phase0(w, h, channels, radius, pixels, buffer, vmin, vmax, dv)
			print('new phase…', datetime.now())
			_fast_blur_2nd_phase0(w, h, channels, radius, pixels, buffer, vmin, vmax, dv)
		else:
			print('bruh moment')
		print('blur ended', datetime.now())

	# TODO add comments
	return original

################################################################################
# "4 threads" version ##########################################################

def _fast_blur_1st_phase2(w, h, channels, radius, pixels, buffer, vmin, vmax, dv):
	NB_THREADS = 4
	t1 = [None] * NB_THREADS
	y_end = 0
	y1 = int(h / NB_THREADS)
	for x in range(0, w):
		vmin[x] = min(x + radius + 1, w - 1)
		vmax[x] = max(x - radius, 0)
	for t in range(0, NB_THREADS):
		y_start = y_end
		y_end = (t+1) * y1
		t1[t] = threading.Thread(target=_blur_rows, args=(x, y_start, y_end, \
		                   w, channels, radius, pixels, buffer, vmin, vmax, dv))
	for t in range(0, NB_THREADS):
		t1[t].start()
	# print('wait row threads')
	for t in range(0, NB_THREADS):
		t1[t].join()

def _fast_blur_2nd_phase2(w, h, channels, radius, pixels, buffer, vmin, vmax, dv):
	NB_THREADS = 4
	t2 = [None] * NB_THREADS
	x_end = 0
	x1 = int(w / NB_THREADS)
	# print('will launch col threads', datetime.now())
	for y in range(0, h):
		vmin[y] = min(y + radius + 1, h - 1) * w
		vmax[y] = max (y - radius, 0) * w
	for t in range(0, NB_THREADS):
		x_start = x_end
		x_end = (t+1) * x1
		t2[t] = threading.Thread(target=_blur_cols, args=(x_start, x_end, y, \
		                w, h, channels, radius, pixels, buffer, vmin, vmax, dv))
	for t in range(0, NB_THREADS):
		t2[t].start()
	# print('wait col threads')
	for t in range(0, NB_THREADS):
		t2[t].join()

def _blur_rows(x, y0, y1, w, channels, radius, pixels, buffer, vmin, vmax, dv):
	# print('row thread with', y0, y1, '(begin)')
	for y in range(y0, y1):
		cur_pixel = y * w * channels
		asum = radius * pixels[cur_pixel + 0]
		rsum = radius * pixels[cur_pixel + 1]
		gsum = radius * pixels[cur_pixel + 2]
		bsum = radius * pixels[cur_pixel + 3]
		for i in range(0, radius+1):
			asum = asum + pixels[cur_pixel + 0]
			rsum = rsum + pixels[cur_pixel + 1]
			gsum = gsum + pixels[cur_pixel + 2]
			bsum = bsum + pixels[cur_pixel + 3]
			cur_pixel = cur_pixel + channels
		cur_pixel = y * w * channels
		for x in range(0, w):
			p1 = (y * w + vmin[x]) * channels
			p2 = (y * w + vmax[x]) * channels
			buffer[cur_pixel + 0] = dv[asum]
			buffer[cur_pixel + 1] = dv[rsum]
			buffer[cur_pixel + 2] = dv[gsum]
			buffer[cur_pixel + 3] = dv[bsum]
			asum = asum + pixels[p1 + 0] - pixels[p2 + 0]
			rsum = rsum + pixels[p1 + 1] - pixels[p2 + 1]
			gsum = gsum + pixels[p1 + 2] - pixels[p2 + 2]
			bsum = bsum + pixels[p1 + 3] - pixels[p2 + 3]
			cur_pixel += channels
	# print('row thread with', y0, y1, '(end)')

def _blur_cols(x0, x1, y, w, h, channels, radius, pixels, buffer, vmin, vmax, dv):
	# print('col thread with', x0, x1, '(begin)')
	for x in range(x0, x1):
		cur_pixel = x * channels
		asum = radius * buffer[cur_pixel + 0]
		rsum = radius * buffer[cur_pixel + 1]
		gsum = radius * buffer[cur_pixel + 2]
		bsum = radius * buffer[cur_pixel + 3]
		for i in range(0, radius+1):
			asum = asum + buffer[cur_pixel + 0]
			rsum = rsum + buffer[cur_pixel + 1]
			gsum = gsum + buffer[cur_pixel + 2]
			bsum = bsum + buffer[cur_pixel + 3]
			cur_pixel = cur_pixel + w * channels
		cur_pixel = x * channels
		for y in range(0, h):
			p1 = (x + vmin[y]) * channels
			p2 = (x + vmax[y]) * channels
			pixels[cur_pixel + 0] = dv[asum]
			pixels[cur_pixel + 1] = dv[rsum]
			pixels[cur_pixel + 2] = dv[gsum]
			pixels[cur_pixel + 3] = dv[bsum]
			asum = asum + buffer[p1 + 0] - buffer[p2 + 0]
			rsum = rsum + buffer[p1 + 1] - buffer[p2 + 1]
			gsum = gsum + buffer[p1 + 2] - buffer[p2 + 2]
			bsum = bsum + buffer[p1 + 3] - buffer[p2 + 3]
			cur_pixel = cur_pixel + w * channels
	# print('col thread with', x0, x1, '(end)')

################################################################################
# "too much threads" version ###################################################

def _fast_blur_1st_phase0(w, h, channels, radius, pixels, buffer, vmin, vmax, dv):
	t1 = [None] * h
	for x in range(0, w):
		vmin[x] = min(x + radius + 1, w - 1)
		vmax[x] = max(x - radius, 0)
	for y in range(0, h):
		t1[y] = threading.Thread(target=_blur_row, args=(x, y, w, channels, \
			                            radius, pixels, buffer, vmin, vmax, dv))
		t1[y].start()
	# print('wait row threads')
	for y in range(0, h):
		t1[y].join()

def _fast_blur_2nd_phase0(w, h, channels, radius, pixels, buffer, vmin, vmax, dv):
	t2 = [None] * w
	# print('will launch col threads', datetime.now())
	for y in range(0, h):
		vmin[y] = min(y + radius + 1, h - 1) * w
		vmax[y] = max (y - radius, 0) * w
	for x in range(0, w):
		t2[x] = threading.Thread(target=_blur_column, args=(x, y, w, h, \
			                  channels, radius, pixels, buffer, vmin, vmax, dv))
		t2[x].start()
	# print('wait col threads')
	for x in range(0, w):
		t2[x].join()

def _blur_row(x, y, w, channels, radius, pixels, buffer, vmin, vmax, dv):
	# print('thread row', y, 'begins')
	cur_pixel = y * w * channels
	asum = radius * pixels[cur_pixel + 0]
	rsum = radius * pixels[cur_pixel + 1]
	gsum = radius * pixels[cur_pixel + 2]
	bsum = radius * pixels[cur_pixel + 3]
	for i in range(0, radius+1):
		asum = asum + pixels[cur_pixel + 0]
		rsum = rsum + pixels[cur_pixel + 1]
		gsum = gsum + pixels[cur_pixel + 2]
		bsum = bsum + pixels[cur_pixel + 3]
		cur_pixel = cur_pixel + channels
	cur_pixel = y * w * channels
	for x in range(0, w):
		p1 = (y * w + vmin[x]) * channels
		p2 = (y * w + vmax[x]) * channels
		buffer[cur_pixel + 0] = dv[asum]
		buffer[cur_pixel + 1] = dv[rsum]
		buffer[cur_pixel + 2] = dv[gsum]
		buffer[cur_pixel + 3] = dv[bsum]
		asum = asum + pixels[p1 + 0] - pixels[p2 + 0]
		rsum = rsum + pixels[p1 + 1] - pixels[p2 + 1]
		gsum = gsum + pixels[p1 + 2] - pixels[p2 + 2]
		bsum = bsum + pixels[p1 + 3] - pixels[p2 + 3]
		cur_pixel += channels
	# print('thread row', y, 'ends')

def _blur_column(x, y, w, h, channels, radius, pixels, buffer, vmin, vmax, dv):
	# print('thread col', x, 'begins')
	cur_pixel = x * channels
	asum = radius * buffer[cur_pixel + 0]
	rsum = radius * buffer[cur_pixel + 1]
	gsum = radius * buffer[cur_pixel + 2]
	bsum = radius * buffer[cur_pixel + 3]
	for i in range(0, radius+1):
		asum = asum + buffer[cur_pixel + 0]
		rsum = rsum + buffer[cur_pixel + 1]
		gsum = gsum + buffer[cur_pixel + 2]
		bsum = bsum + buffer[cur_pixel + 3]
		cur_pixel = cur_pixel + w * channels
	cur_pixel = x * channels
	for y in range(0, h):
		p1 = (x + vmin[y]) * channels
		p2 = (x + vmax[y]) * channels
		pixels[cur_pixel + 0] = dv[asum]
		pixels[cur_pixel + 1] = dv[rsum]
		pixels[cur_pixel + 2] = dv[gsum]
		pixels[cur_pixel + 3] = dv[bsum]
		asum = asum + buffer[p1 + 0] - buffer[p2 + 0]
		rsum = rsum + buffer[p1 + 1] - buffer[p2 + 1]
		gsum = gsum + buffer[p1 + 2] - buffer[p2 + 2]
		bsum = bsum + buffer[p1 + 3] - buffer[p2 + 3]
		cur_pixel = cur_pixel + w * channels
	# print('thread col', x, 'ends')

################################################################################
# "only 1 thread" version ######################################################

def _fast_blur_1st_phase1(w, h, channels, radius, pixels, buffer, vmin, vmax, dv):
	for x in range(0, w):
		vmin[x] = min(x + radius + 1, w - 1)
		vmax[x] = max(x - radius, 0)
	for y in range(0, h):
		cur_pixel = y * w * channels
		asum = radius * pixels[cur_pixel + 0]
		rsum = radius * pixels[cur_pixel + 1]
		gsum = radius * pixels[cur_pixel + 2]
		bsum = radius * pixels[cur_pixel + 3]
		for i in range(0, radius+1):
			asum = asum + pixels[cur_pixel + 0]
			rsum = rsum + pixels[cur_pixel + 1]
			gsum = gsum + pixels[cur_pixel + 2]
			bsum = bsum + pixels[cur_pixel + 3]
			cur_pixel = cur_pixel + channels
		cur_pixel = y * w * channels
		for x in range(0, w):
			p1 = (y * w + vmin[x]) * channels
			p2 = (y * w + vmax[x]) * channels
			buffer[cur_pixel + 0] = dv[asum]
			buffer[cur_pixel + 1] = dv[rsum]
			buffer[cur_pixel + 2] = dv[gsum]
			buffer[cur_pixel + 3] = dv[bsum]
			asum = asum + pixels[p1 + 0] - pixels[p2 + 0]
			rsum = rsum + pixels[p1 + 1] - pixels[p2 + 1]
			gsum = gsum + pixels[p1 + 2] - pixels[p2 + 2]
			bsum = bsum + pixels[p1 + 3] - pixels[p2 + 3]
			cur_pixel += channels

def _fast_blur_2nd_phase1(w, h, channels, radius, pixels, buffer, vmin, vmax, dv):
	for y in range(0, h):
		vmin[y] = min(y + radius + 1, h - 1) * w
		vmax[y] = max (y - radius, 0) * w
	for x in range(0, w):
		cur_pixel = x * channels
		asum = radius * buffer[cur_pixel + 0]
		rsum = radius * buffer[cur_pixel + 1]
		gsum = radius * buffer[cur_pixel + 2]
		bsum = radius * buffer[cur_pixel + 3]
		for i in range(0, radius+1):
			asum = asum + buffer[cur_pixel + 0]
			rsum = rsum + buffer[cur_pixel + 1]
			gsum = gsum + buffer[cur_pixel + 2]
			bsum = bsum + buffer[cur_pixel + 3]
			cur_pixel = cur_pixel + w * channels
		cur_pixel = x * channels
		for y in range(0, h):
			p1 = (x + vmin[y]) * channels
			p2 = (x + vmax[y]) * channels
			pixels[cur_pixel + 0] = dv[asum]
			pixels[cur_pixel + 1] = dv[rsum]
			pixels[cur_pixel + 2] = dv[gsum]
			pixels[cur_pixel + 3] = dv[bsum]
			asum = asum + buffer[p1 + 0] - buffer[p2 + 0]
			rsum = rsum + buffer[p1 + 1] - buffer[p2 + 1]
			gsum = gsum + buffer[p1 + 2] - buffer[p2 + 2]
			bsum = bsum + buffer[p1 + 3] - buffer[p2 + 3]
			cur_pixel = cur_pixel + w * channels

################################################################################

