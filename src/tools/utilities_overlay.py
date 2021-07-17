# utilities_overlay.py
#
# Copyright 2018-2021 Romain F. T.
#
# GPL 3

import cairo, math
from gi.repository import Gdk, GdkPixbuf
from .selection_manager import NoSelectionPathException

################################################################################
# Selection overlay ############################################################

def utilities_show_overlay_on_context(ccontext, cpath, is_dashed, thickness=1):
	"""Draw a blueish area on `ccontext`, with or without dashes. This is mainly
	used for the selection, but also for the minimap."""
	if cpath is None:
		raise NoSelectionPathException()
	ccontext.new_path()
	ccontext.set_line_width(thickness)
	if is_dashed:
		ccontext.set_dash([thickness * 3, thickness * 3])
	ccontext.append_path(cpath)
	ccontext.set_source_rgba(0.1, 0.1, 0.3, 0.2)
	ccontext.fill_preserve()
	ccontext.set_source_rgba(0.5, 0.5, 0.5, 0.5)
	ccontext.stroke()

################################################################################
# Transform tools overlay ######################################################

def utilities_show_handles_on_context(cairo_context, x1, x2, y1, y2, thickness=1):
	"""Request the drawing of handles for a rectangle pixbuf having the provided
	coords. Handles are only decorative objects drawn on the surface to help the
	user understand the rationale of tools without relying on the mouse cursor."""
	rayon = min([(x2 - x1)/5, (y2 - y1)/5, 12 * thickness])
	lateral_handles = True # may be a parameter later
	if rayon < 4 * thickness:
		cairo_context.set_line_width(thickness)
	elif rayon < 8 * thickness:
		cairo_context.set_line_width(2 * thickness)
	else:
		cairo_context.set_line_width(3 * thickness)

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

	cairo_context.set_line_width(thickness)
	cairo_context.set_dash([2 * thickness, 2 * thickness])
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
	cairo_context.set_source_rgba(1.0, 1.0, 1.0, 1.0)
	cairo_context.fill_preserve()
	cairo_context.set_source_rgba(0.5, 0.5, 0.5, 0.5)
	cairo_context.stroke()

################################################################################
# Canvas generic ouline ########################################################

def utilities_generic_canvas_outline(cairo_context, w, h, zoom_level):
	cairo_context.set_source_rgba(0.0, 0.0, 0.0, 1.0)
	cairo_context.set_dash([])
	size = max(1, int(1 / zoom_level))
	cairo_context.set_line_width(size)
	cairo_context.move_to(w + size, 0)
	cairo_context.rel_line_to(0, h + size)
	cairo_context.line_to(0, h + size)
	cairo_context.stroke_preserve()

	cairo_context.set_source_rgba(1.0, 1.0, 1.0, 1.0)
	cairo_context.set_dash([2 * size, 2 * size])
	cairo_context.stroke()

################################################################################

