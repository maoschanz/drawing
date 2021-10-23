# utilities_paths.py
#
# Copyright 2018-2021 Romain F. T.
#
# GPL 3

import cairo, math
from gi.repository import Gdk, GdkPixbuf
from .message_dialog import DrMessageDialog

################################################################################

def utilities_get_rgba_for_xy(surface, x, y):
	# Guard clause: we can't perform color picking outside of the surface
	if x < 0 or x > surface.get_width() or y < 0 or y > surface.get_height():
		return None
	screenshot = Gdk.pixbuf_get_from_surface(surface, float(x), float(y), 1, 1)
	rgba_vals = screenshot.get_pixels()
	return rgba_vals

def utilities_get_magic_path(surface, x, y, window, coef):
	"""This method tries to build a path defining an area of the same color. It
	will mainly be used to paint this area, or to select it."""
	cairo_context = cairo.Context(surface)
	old_color = utilities_get_rgba_for_xy(surface, x, y)

	# Cairo doesn't provide methods for what we want to do. I will have to
	# define myself how to decide what should be filled.
	# The heuristic here is that we create a hull containing the area of
	# color we want to paint. We don't care about "enclaves" of other colors.
	while (utilities_get_rgba_for_xy(surface, x, y) == old_color) and y > 0:
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
			if (utilities_get_rgba_for_xy(surface, future_x, future_y) == old_color) \
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
		# print('direction :', direction)
		if (new_x != -10):
			cairo_context.line_to(x, y)
		# else:
		#	 print("TENTATIVE ABUSIVE D'AJOUT")
		#	 should_stop = True

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
	# print('i: ' + str(i))
	return cairo_context.copy_path()

def launch_infinite_loop_dialog(window):
	dialog = DrMessageDialog(window)
	cancel_id = dialog.set_action(_("Cancel"), None)
	continue_id = dialog.set_action(_("Continue"), None, True)
	dialog.add_string(_("The area seems poorly delimited, or is very complex."))
	dialog.add_string(_("This algorithm may not be able to manage the wanted area."))
	dialog.add_string(_("Do you want to abort the operation, or to let the tool struggle ?"))
	return dialog, continue_id

################################################################################

# The coordinates of the corners of the triangle. These points are defined as if
# the end of the arrow line is at "0, 0" and rotated by 0 degrees.
ARROW_TRIANGLE = [
	(0.0, 0.0),
	(-2.747, 1.0),
	(-2.747, -1.0),
]

MIN_ARROW_SCALE = 3

def utilities_add_arrow_triangle(cairo_context, x2, y2, x1, y1, line_width):
	"""Adds a triangular head to the current path."""
	if x1 == x2 and y1 == y2:
		line_angle = 0
	else:
		line_angle = math.atan2(y2 - y1, x2 - x1)
	sin, cos = math.sin(line_angle), math.cos(line_angle)

	# FIXME cases with very short last segment
	# if scale == line_width, dashed arrow will look like shit
	scale = max(line_width * 1.1, MIN_ARROW_SCALE)

	# when the last segment of the line is very short, the head is scaled down
	# last_segment_length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
	# scale = min(scale, last_segment_length/line_width)
	# ^XXX broken with dashes
	# TODO ça peut ne plus être nécessaire si je décale la tête

	head = []
	# scale, rotate and translate the arrow triangle
	for x, y in ARROW_TRIANGLE:
		p = (x * scale, y * scale)
		p = (p[0] * cos - p[1] * sin, p[0] * sin + p[1] * cos)
		p = (p[0] + x2, p[1] + y2)
		head.append(p)

	# draw the arrow triangle
	_draw_head(cairo_context, head, True)

	# shameful hack to get a full head in cases where the line is dashed
	if cairo_context.get_dash_count() > 0:
		_draw_head(cairo_context, head, False)
		_draw_head(cairo_context, head, False)
		_draw_head(cairo_context, head, False)
		_draw_head(cairo_context, head, False)

	# XXX the path isn't filled because the path is opened by the first point of
	# the line/curve and it can't be closed so easily
	cairo_context.close_path()
	# The stroke must be done afterwards, by the calling method

def _draw_head(cairo_context, head, first_try):
	if first_try:
		cairo_context.move_to(*head[0])
	else:
		cairo_context.line_to(*head[0])
	cairo_context.line_to(*head[1])
	cairo_context.line_to(*head[2])

################################################################################
# Path smoothing ###############################################################

def utilities_smooth_path(cairo_context, cairo_path):
	"""Extrapolate a path made of straight lines into a path made of curves. New
	points are added according to the length of the line it replaces, the length
	of the previous one, and the length of the next one."""
	x1 = y1 = None
	x2 = y2 = None
	x3 = y3 = None
	x4 = y4 = None
	for pts in cairo_path:
		if pts[1] == ():
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

