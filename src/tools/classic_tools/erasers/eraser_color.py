# Licensed under GPL3 https://github.com/maoschanz/drawing/blob/master/LICENSE

import cairo
from .abstract_eraser import AbstractEraser
from .utilities_paths import utilities_get_rgba_for_xy

class EraserColor(AbstractEraser):
	__gtype_name__ = 'EraserColor'

	def __init__(self, tool):
		super().__init__()
		self._tool = tool

	def get_label_options(self, options={}):
		return _("Remove color")

	def on_motion(self, cairo_context, press, event, path=None):
		pass

	def on_release(self, cairo_context, press, event, path=None):
		return utilities_get_rgba_for_xy(self._tool.get_surface(), *event)

	############################################################################

	def do_operation(self, cairo_context, operation):
		"""Replace the color with transparency by adding an alpha channel."""
		old_rgba = operation['path']
		r0 = old_rgba[0]
		g0 = old_rgba[1]
		b0 = old_rgba[2]
		# ^ it's not possible to take into account the alpha channel
		margin = 0 # XXX as an option ? is not elegant but it's powerful
		self._clip_red(margin, r0, g0, b0)
		self._tool.restore_pixbuf()
		self._tool.non_destructive_show_modif()

	def _clip_red(self, margin, r0, g0, b0):
		for i in range(-1 * margin, margin + 1):
			r = r0 + i
			if r <= 255 and r >= 0:
				self._clip_green(margin, r, g0, b0)

	def _clip_green(self, margin, r, g0, b0):
		for i in range(-1 * margin, margin + 1):
			g = g0 + i
			if g <= 255 and g >= 0:
				self._clip_blue(margin, r, g, b0)

	def _clip_blue(self, margin, r, g, b0):
		for i in range(-1 * margin, margin + 1):
			b = b0 + i
			if b <= 255 and b >= 0:
				self._replace_main_with_alpha(r, g, b)

	def _replace_main_with_alpha(self, red, green, blue):
		new_pixbuf = self._tool.get_main_pixbuf().add_alpha(True, red, green, blue)
		self._tool.get_image().set_main_pixbuf(new_pixbuf)

	############################################################################
################################################################################

