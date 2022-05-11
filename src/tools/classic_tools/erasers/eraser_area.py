# Licensed under GPL3 https://github.com/maoschanz/drawing/blob/master/LICENSE

import cairo
from .abstract_eraser import AbstractEraser

class EraserArea(AbstractEraser):
	__gtype_name__ = 'EraserArea'

	def __init__(self, **kwargs):
		super().__init__()

	############################################################################
################################################################################

