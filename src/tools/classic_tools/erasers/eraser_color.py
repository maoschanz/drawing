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

	# XXX on_motion pourrait foreach entre le point courant et le précédent ?

	def on_release(self, cairo_context, press, event, path=None):
		# in this eraser, "path" is actually a list of rgba
		if path is None:
			path = []
		new_rgba = utilities_get_rgba_for_xy(self._tool.get_surface(), *event)
		if new_rgba[3] == 0:
			# no need to erase what's already erased
			return path
		path.append(new_rgba)
		return path

	############################################################################

	def do_operation(self, cairo_context, operation):
		"""Replace the color with transparency by adding an alpha channel."""
		all_rgbas = operation['path']
		for rgba in all_rgbas:
			self._erase_rgb(rgba[0:3])
			# ^ it's not possible to take into account the alpha channel :(

	def _erase_rgb(self, rgb0, margin=0):
		self._clip_red(*rgb0, margin)
		self._tool.restore_pixbuf()
		self._tool.non_destructive_show_modif()

	def _clip_red(self, r0, g0, b0, margin=0):
		for i in range(-1 * margin, margin + 1):
			r = r0 + i
			if r <= 255 and r >= 0:
				self._clip_green(r, g0, b0, margin)

	def _clip_green(self, r, g0, b0, margin=0):
		for i in range(-1 * margin, margin + 1):
			g = g0 + i
			if g <= 255 and g >= 0:
				self._clip_blue(r, g, b0, margin)

	def _clip_blue(self, r, g, b0, margin=0):
		for i in range(-1 * margin, margin + 1):
			b = b0 + i
			if b <= 255 and b >= 0:
				self._replace_main_with_alpha(r, g, b)

	def _replace_main_with_alpha(self, red, green, blue):
		new_pixbuf = self._tool.get_main_pixbuf().add_alpha(True, red, green, blue)
		self._tool.get_image().set_main_pixbuf(new_pixbuf)

	############################################################################
################################################################################

