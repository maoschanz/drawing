# utilities_tools.py
#
# Copyright 2018-2020 Romain F. T.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import cairo, math
from gi.repository import Gdk, GdkPixbuf
from .message_dialog import DrawingMessageDialog

################################################################################
# Selection overlay ############################################################

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
		#	 print('TENTATIVE ABUSIVE D\'AJOUT')
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
	dialog = DrawingMessageDialog(window)
	cancel_id = dialog.set_action(_("Cancel"), None, False)
	continue_id = dialog.set_action(_("Continue"), None, True)
	dialog.add_string(_("The area seems poorly delimited, or is very complex."))
	dialog.add_string(_("This algorithm may not be able to manage the wanted area."))
	dialog.add_string(_("Do you want to abort the operation, or to let the tool struggle ?"))
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
	if line_length == 0:
		return
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
	x1 = y1 = None
	x2 = y2 = None
	x3 = y3 = None
	x4 = y4 = None
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

