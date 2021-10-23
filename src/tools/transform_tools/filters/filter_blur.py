# Licensed under GPL3 https://github.com/maoschanz/drawing/blob/master/LICENSE

from gi.repository import Gdk
from .abstract_filter import AbstractFilter
from .utilities_blur import utilities_blur_surface, BlurType, BlurDirection

class FilterBlur(AbstractFilter):
	__gtype_name__ = 'FilterBlur'

	def __init__(self, filter_id, filters_tool, *args):
		super().__init__(filter_id, filters_tool)
		self._blur_direction = BlurDirection.INVALID
		self._label, self._spinbtn = self._tool.bar.add_spinbtn( \
		                        _("Blur radius"), [5, 1, 99, 1, 10, 0], 2, 'px')
		# it's [value, lower, upper, step_increment, page_increment, page_size]

	def get_preferred_minimum_width(self):
		return self._label.get_preferred_width()[0] + \
		     self._spinbtn.get_preferred_width()[0]

	def set_filter_compact(self, is_active, is_compact):
		self._label.set_visible(is_active and not is_compact)
		self._spinbtn.set_visible(is_active)

	def set_attributes_values(self):
		state_as_string = self._tool.get_option_value('filters_blur_dir')
		if state_as_string == 'none':
			self._blur_direction = BlurDirection.BOTH
		elif state_as_string == 'horizontal':
			self._blur_direction = BlurDirection.HORIZONTAL
		elif state_as_string == 'vertical':
			self._blur_direction = BlurDirection.VERTICAL
		else:
			self._blur_direction = BlurDirection.INVALID

	def build_filter_op(self):
		options = {
			'blur_algo': self._tool.blur_algo,
			'blur_direction': self._blur_direction,
			'radius': self._spinbtn.get_value_as_int()
		}
		return options

	def do_filter_operation(self, source_pixbuf, operation):
		blur_algo = operation['blur_algo']
		if blur_algo == BlurType.INVALID:
			return
		b_radius = operation['radius']
		b_direction = operation['blur_direction']

		surface = Gdk.cairo_surface_create_from_pixbuf(source_pixbuf, 0, None)
		scale = self._tool.scale_factor()
		surface.set_device_scale(scale, scale)

		bs = utilities_blur_surface(surface, b_radius, blur_algo, b_direction)
		bp = Gdk.pixbuf_get_from_surface(bs, 0, 0, bs.get_width(), bs.get_height())
		self._tool.get_image().set_temp_pixbuf(bp)

	############################################################################
################################################################################

