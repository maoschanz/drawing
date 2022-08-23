# Licensed under GPL3 https://github.com/maoschanz/drawing/blob/master/LICENSE

import cairo

class AbstractEraser():
	__gtype_name__ = 'AbstractEraser'

	def __init__(self):
		pass

	def get_label_options(self, options={}):
		pass

	def get_active_options(self):
		return []

	def use_size(self):
		return False

	def on_motion(self, cairo_context, press, event, path=None):
		return self.on_release(cairo_context, press, event, path)

	def on_release(self, cairo_context, press, event, path=None):
		return None

	def do_operation(self, cairo_context, operation):
		pass

	############################################################################
################################################################################

