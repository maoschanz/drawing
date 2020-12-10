# Licensed under GPL3 https://github.com/maoschanz/drawing/blob/master/LICENSE

class AbstractFilter():
	__gtype_name__ = 'AbstractFilter'

	def __init__(self, filter_id, filters_tool, *args):
		self._id = filter_id
		self._tool = filters_tool

	def get_preferred_minimum_width(self):
		return 0

	def set_filter_compact(self, is_active, is_compact):
		pass

	def set_attributes_values(self):
		pass

	def build_filter_op(self):
		return {}

	def do_filter_operation(self, source_pixbuf, operation):
		pass

	############################################################################
################################################################################

