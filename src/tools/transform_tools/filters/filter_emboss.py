# Licensed under GPL3 https://github.com/maoschanz/drawing/blob/master/LICENSE

import cairo
from gi.repository import Gdk
from .abstract_filter import AbstractFilter
from .utilities_blur import utilities_blur_surface, BlurType, BlurDirection

class FilterEmboss(AbstractFilter):
	__gtype_name__ = 'FilterEmboss'

	def do_filter_operation(self, source_pixbuf, operation):
		surface = Gdk.cairo_surface_create_from_pixbuf(source_pixbuf, 0, None)
		scale = self._tool.scale_factor()
		surface.set_device_scale(scale, scale)
		width = source_pixbuf.get_width()
		height = source_pixbuf.get_height()
		new_surface = cairo.ImageSurface(cairo.Format.ARGB32, width, height)

		cairo_context = cairo.Context(new_surface)
		cairo_context.set_source_surface(surface)
		cairo_context.set_operator(cairo.Operator.SOURCE)
		cairo_context.paint()

		bdir = BlurDirection.BOTH # could be an option
		bs = utilities_blur_surface(surface, 1, BlurType.CAIRO_REPAINTS, bdir)
		cairo_context2 = cairo.Context(bs)
		cairo_context2.set_operator(cairo.Operator.DIFFERENCE)
		cairo_context2.set_source_rgba(1.0, 1.0, 1.0, 1.0)
		cairo_context2.paint()

		cairo_context.set_source_surface(bs)
		cairo_context.set_operator(cairo.Operator.OVER)
		cairo_context.paint_with_alpha(0.5)

		new_pixbuf = Gdk.pixbuf_get_from_surface(new_surface, 0, 0, \
		                      new_surface.get_width(), new_surface.get_height())
		self._tool.get_image().set_temp_pixbuf(new_pixbuf)

	############################################################################
################################################################################

