# utilities_overlay.py
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
