# Licensed under GPL3 https://github.com/maoschanz/drawing/blob/master/LICENSE

import cairo
from gi.repository import Gdk
from .abstract_filter import AbstractFilter

class FilterVeil(AbstractFilter):
	__gtype_name__ = 'FilterVeil'

	def do_filter_operation(self, source_pixbuf, operation):
		self._tool.get_image().set_temp_pixbuf(source_pixbuf.copy())
		temp = self._tool.get_image().temp_pixbuf
		source_pixbuf.saturate_and_pixelate(temp, 1, True)

	############################################################################
################################################################################

