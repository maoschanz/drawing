# utilities_tools.py

import cairo, math, threading
from gi.repository import Gtk, Gdk, GdkPixbuf
from datetime import datetime # Not actually needed, just to measure perfs XXX
from .message_dialog import DrawingMessageDialog

################################################################################

def utilities_get_rgb_for_xy(surface, x, y): # TODO use gdkpixbuf data to get an alpha
	# Guard clause: we can't perform color picking outside of the surface
	if x < 0 or x > surface.get_width() or y < 0 or y > surface.get_height():
		return [-1,-1,-1]
	screenshot = Gdk.pixbuf_get_from_surface(surface, float(x), float(y), 1, 1)
	rgb_vals = screenshot.get_pixels()
	return rgb_vals # array de 3 valeurs, de 0 à 255

################################################################################

def utilities_show_overlay_on_context(cairo_context, cairo_path, has_dashes):
	"""Draw a blueish area on `cairo_context`, with or without dashes. This is
	mainly used for the selection."""
	if cairo_path is None:
		return # TODO throw an exception
	cairo_context.new_path()
	cairo_context.set_line_width(1)
	if has_dashes:
		cairo_context.set_dash([3, 3])
	cairo_context.append_path(cairo_path)
	cairo_context.set_source_rgba(0.1, 0.1, 0.3, 0.2)
	cairo_context.fill_preserve()
	cairo_context.set_source_rgba(0.5, 0.5, 0.5, 0.5)
	cairo_context.stroke()

def utilities_show_handles_on_context(cairo_context, x1, x2, y1, y2):
	"""Request the drawing of handles for a rectangle pixbuf having the provided
	coords. Handles are only decorative objects drawn on the surface to help the
	user understand the rationale of tools without relying on the mouse cursor."""
	rayon = min([(x2 - x1)/5, (y2 - y1)/5, 12])
	lateral_handles = True # may be a parameter later

	_draw_arc_handle(cairo_context, x1, y1, rayon, 'nw')
	_draw_arc_handle(cairo_context, x2, y1, rayon, 'ne')
	_draw_arc_handle(cairo_context, x2, y2, rayon, 'se')
	_draw_arc_handle(cairo_context, x1, y2, rayon, 'sw')
	if lateral_handles:
		_draw_arc_handle(cairo_context, (x1+x2)/2, y1, rayon, 'n')
		_draw_arc_handle(cairo_context, x2, (y1+y2)/2, rayon, 'e')
		_draw_arc_handle(cairo_context, (x1+x2)/2, y2, rayon, 's')
		_draw_arc_handle(cairo_context, x1, (y1+y2)/2, rayon, 'w')

	cairo_context.move_to(x1, y1)
	cairo_context.line_to(x1, y2)
	cairo_context.line_to(x2, y2)
	cairo_context.line_to(x2, y1)
	cairo_context.close_path()

	cairo_context.set_line_width(1)
	cairo_context.set_dash([2, 2])
	cairo_context.set_source_rgba(0.5, 0.5, 0.5, 0.5)
	cairo_context.stroke()

def _draw_arc_handle(cairo_context, x, y, rayon, orientation):
	"""Draw a moon-like shape with the given orientation and radius. The coords
	are the center of the shape. The orientation is an enumeration provided as a
	string with the stupid n/nw/w/sw/s/se/e/ne format."""
	if orientation == 'nw':
		angle_1 = 0.5 * math.pi
		angle_2 = 2.0 * math.pi
	elif orientation == 'n':
		angle_1 = math.pi
		angle_2 = 0.0
	elif orientation == 'ne':
		angle_1 = math.pi
		angle_2 = 0.5 * math.pi
	elif orientation == 'e':
		angle_1 = -0.5 * math.pi
		angle_2 = 0.5 * math.pi
	elif orientation == 'se':
		angle_1 = -0.5 * math.pi
		angle_2 = math.pi
	elif orientation == 's':
		angle_1 = 0.0
		angle_2 = math.pi
	elif orientation == 'sw':
		angle_1 = 0.0
		angle_2 = -0.5 * math.pi
	elif orientation == 'w':
		angle_1 = 0.5 * math.pi
		angle_2 = -0.5 * math.pi

	cairo_context.move_to(x, y)
	cairo_context.arc(x, y, rayon, angle_1, angle_2)
	cairo_context.close_path()

	cairo_context.set_line_width(3)
	cairo_context.set_source_rgba(1.0, 1.0, 1.0, 1.0)
	cairo_context.fill_preserve()
	cairo_context.set_source_rgba(0.5, 0.5, 0.5, 0.5)
	cairo_context.stroke()

def utilities_get_magic_path2(surface, x, y, window, coef):
	# TODO idée :
	# le délire ce serait de commencer un path petit, puis de l'étendre avec
	# cairo.Context.clip_extents() jusqu'à ce qu'on soit à fond.
	# À partir de là on fait cairo.Context.paint()
	pass

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
	dialog.add_string(_("The area seems poorly delimited, or is very complex."))
	dialog.add_string(_("This algorithm may not be able to manage the wanted area."))
	dialog.add_string(_("Do you want to abort the operation, or to let the tool struggle ?"))
	return dialog, continue_id

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

################################################################################
# Path smoothing ###############################################################

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
# Blurring algorithms ##########################################################

class BlurType():
	BOX = 0
	HORIZONTAL = 1
	VERTICAL = 2
	EXPERIMENTAL = 3
	INVALID = 10

def utilities_fast_blur(surface, radius, iterations, algotype):
	"""This is the 'official' method to access the blur algorithms. The last
	argument is an integer corresponding to a BlurType enumeration."""
	if algotype == BlurType.INVALID:
		return
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
	# multithreading (i'm quite sure the access to buffers are not safe at all).
	# The 2 phases of the algo have been separated to allow directional blur.
	original = cairo.ImageSurface(cairo.Format.ARGB32, w, h)
	cairo_context = cairo.Context(original)
	# cairo_context.set_operator(cairo.Operator.SOURCE)
	cairo_context.set_source_surface(surface, 0, 0)
	cairo_context.paint()
	original.flush()
	pixels = original.get_data()

	buffer0 = [None] * (w * h * channels)
	vmin = [None] * max(w, h)
	vmax = [None] * max(w, h)
	div = 2 * radius + 1
	dv = [None] * (256 * div)
	for i in range(0, len(dv)):
		dv[i] = int(i / div)

	while iterations > 0:
		iterations = iterations - 1
		time0 = datetime.now()
		print('begin fast blur, using algo n°', algotype)
		if algotype == BlurType.HORIZONTAL:
			full_buff = _fast_blur_1st_phase3(w, h, channels, radius, pixels, vmin, vmax, dv)
			for i in range(0, len(full_buff)):
				pixels[i] = full_buff[i] # XXX useful?
		elif algotype == BlurType.VERTICAL:
			for i in range(0, len(pixels)):
				buffer0[i] = pixels[i] # XXX useful?
			_fast_blur_2nd_phase1(w, h, channels, radius, pixels, buffer0, vmin, vmax, dv)
		elif algotype == BlurType.EXPERIMENTAL:
			# 4+1 threads
			# TODO despite being multithreaded, the first phase is slower than BlurType.BOX
			full_buff = _fast_blur_1st_phase3(w, h, channels, radius, pixels, vmin, vmax, dv)
			# print('end of the 1st phase…', datetime.now() - time0)
			_fast_blur_2nd_phase1(w, h, channels, radius, pixels, full_buff, vmin, vmax, dv)
		else: # if algotype == BlurType.BOX:
			# no multi-threading
			_fast_blur_1st_phase1(w, h, channels, radius, pixels, buffer0, vmin, vmax, dv)
			# print('end of the 1st phase…', datetime.now() - time0)
			_fast_blur_2nd_phase1(w, h, channels, radius, pixels, buffer0, vmin, vmax, dv)
		time1 = datetime.now()
		print('fast blur ended, total time:', time1 - time0)
	return original

################################################################################
# mixed solution version

def _fast_blur_1st_phase3(w, h, channels, radius, pixels, vmin, vmax, dv):
	NB_THREADS = 4
	t1 = [None] * NB_THREADS
	full_buffer = []
	buffers = []
	y_end = 0
	for x in range(0, w):
		vmin[x] = min(x + radius + 1, w - 1)
		vmax[x] = max(x - radius, 0)
	for t in range(0, NB_THREADS):
		y_start = y_end
		if t == NB_THREADS - 1:
			y_end = h
		else:
			y_end = y_start + int(h / NB_THREADS)
		buff_size = w * (y_end - y_start) * channels
		buff = [0] * buff_size
		buffers.append(buff)
		t1[t] = threading.Thread(target=_blur_rows3, args=(x, y_start, y_end, \
		                     w, channels, radius, pixels, buff, vmin, vmax, dv))
	for t in range(0, NB_THREADS):
		t1[t].start()
	for t in range(0, NB_THREADS):
		t1[t].join()
		full_buffer += buffers[t]
	return full_buffer

def _blur_rows3(x, y0, y1, w, channels, radius, pixels, buff0, vmin, vmax, dv):
	# print('row thread with', y0, y1, '(begin)')
	diff = y0 * w * channels
	for y in range(y0, y1):
		cur_pixel = y * w * channels
		asum = radius * pixels[cur_pixel + 0]
		rsum = radius * pixels[cur_pixel + 1]
		gsum = radius * pixels[cur_pixel + 2]
		bsum = radius * pixels[cur_pixel + 3]
		for i in range(0, radius+1):
			asum += pixels[cur_pixel + 0]
			rsum += pixels[cur_pixel + 1]
			gsum += pixels[cur_pixel + 2]
			bsum += pixels[cur_pixel + 3]
			cur_pixel += channels
		cur_pixel = y * w * channels - diff
		for x in range(0, w):
			p1 = (y * w + vmin[x]) * channels
			p2 = (y * w + vmax[x]) * channels
			buff0[cur_pixel + 0] = dv[asum]
			buff0[cur_pixel + 1] = dv[rsum]
			buff0[cur_pixel + 2] = dv[gsum]
			buff0[cur_pixel + 3] = dv[bsum]
			asum += pixels[p1 + 0] - pixels[p2 + 0]
			rsum += pixels[p1 + 1] - pixels[p2 + 1]
			gsum += pixels[p1 + 2] - pixels[p2 + 2]
			bsum += pixels[p1 + 3] - pixels[p2 + 3]
			cur_pixel += channels
	# print('row thread with', y0, y1, '(end)')

################################################################################
# "only 1 thread" version

def _fast_blur_1st_phase1(w, h, channels, radius, pixels, buff0, vmin, vmax, dv):
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
			asum += pixels[cur_pixel + 0]
			rsum += pixels[cur_pixel + 1]
			gsum += pixels[cur_pixel + 2]
			bsum += pixels[cur_pixel + 3]
			cur_pixel += channels
		cur_pixel = y * w * channels
		for x in range(0, w):
			p1 = (y * w + vmin[x]) * channels
			p2 = (y * w + vmax[x]) * channels
			buff0[cur_pixel + 0] = dv[asum]
			buff0[cur_pixel + 1] = dv[rsum]
			buff0[cur_pixel + 2] = dv[gsum]
			buff0[cur_pixel + 3] = dv[bsum]
			asum += pixels[p1 + 0] - pixels[p2 + 0]
			rsum += pixels[p1 + 1] - pixels[p2 + 1]
			gsum += pixels[p1 + 2] - pixels[p2 + 2]
			bsum += pixels[p1 + 3] - pixels[p2 + 3]
			cur_pixel += channels

def _fast_blur_2nd_phase1(w, h, channels, radius, pixels, buff0, vmin, vmax, dv):
	for y in range(0, h):
		vmin[y] = min(y + radius + 1, h - 1) * w
		vmax[y] = max (y - radius, 0) * w
	for x in range(0, w):
		cur_pixel = x * channels
		asum = radius * buff0[cur_pixel + 0]
		rsum = radius * buff0[cur_pixel + 1]
		gsum = radius * buff0[cur_pixel + 2]
		bsum = radius * buff0[cur_pixel + 3]
		for i in range(0, radius+1):
			asum += buff0[cur_pixel + 0]
			rsum += buff0[cur_pixel + 1]
			gsum += buff0[cur_pixel + 2]
			bsum += buff0[cur_pixel + 3]
			cur_pixel += w * channels
		cur_pixel = x * channels
		for y in range(0, h):
			p1 = (x + vmin[y]) * channels
			p2 = (x + vmax[y]) * channels
			pixels[cur_pixel + 0] = dv[asum]
			pixels[cur_pixel + 1] = dv[rsum]
			pixels[cur_pixel + 2] = dv[gsum]
			pixels[cur_pixel + 3] = dv[bsum]
			asum += buff0[p1 + 0] - buff0[p2 + 0]
			rsum += buff0[p1 + 1] - buff0[p2 + 1]
			gsum += buff0[p1 + 2] - buff0[p2 + 2]
			bsum += buff0[p1 + 3] - buff0[p2 + 3]
			cur_pixel += w * channels

################################################################################

