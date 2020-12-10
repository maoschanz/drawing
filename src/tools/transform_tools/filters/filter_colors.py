# Licensed under GPL3 https://github.com/maoschanz/drawing/blob/master/LICENSE

import cairo
from gi.repository import Gdk
from .abstract_filter import AbstractFilter

class FilterColors(AbstractFilter):
	__gtype_name__ = 'FilterColors'

	def __init__(self, filter_id, filters_tool, *args):
		super().__init__(filter_id, filters_tool)

	# this filter could be so much more, but what's pertinent?

	def do_filter_operation(self, source_pixbuf, operation):
		surface = Gdk.cairo_surface_create_from_pixbuf(source_pixbuf, 0, None)
		cairo_context = cairo.Context(surface)
		cairo_context.set_operator(cairo.Operator.DIFFERENCE)
		cairo_context.set_source_rgba(1.0, 1.0, 1.0, 1.0)
		cairo_context.paint()
		new_pixbuf = Gdk.pixbuf_get_from_surface(surface, 0, 0, \
		                              surface.get_width(), surface.get_height())
		self._tool.get_image().set_temp_pixbuf(new_pixbuf)

	############################################################################
################################################################################

