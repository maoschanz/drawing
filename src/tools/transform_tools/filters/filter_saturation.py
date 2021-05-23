# Licensed under GPL3 https://github.com/maoschanz/drawing/blob/master/LICENSE

from .abstract_filter import AbstractFilter

class FilterSaturation(AbstractFilter):
	__gtype_name__ = 'FilterSaturation'

	def __init__(self, filter_id, filters_tool, *args):
		super().__init__(filter_id, filters_tool)
		self._label, self._spinbtn = self._tool.bar.add_spinbtn( \
		                    _("Saturation"), [100, 0, 10000, 10, 30, 0], 3, '%')
		# it's [value, lower, upper, step_increment, page_increment, page_size]

	def get_preferred_minimum_width(self):
		return self._label.get_preferred_width()[0] + \
		     self._spinbtn.get_preferred_width()[0]

	def set_filter_compact(self, is_active, is_compact):
		self._label.set_visible(is_active and not is_compact)
		self._spinbtn.set_visible(is_active)

	def build_filter_op(self):
		options = {
			'percent': self._spinbtn.get_value() / 100,
		}
		return options

	def do_filter_operation(self, source_pixbuf, operation):
		self._tool.get_image().set_temp_pixbuf(source_pixbuf.copy())
		temp = self._tool.get_image().temp_pixbuf
		source_pixbuf.saturate_and_pixelate(temp, operation['percent'], False)

	############################################################################
################################################################################

