# Licensed under GPL3 https://github.com/maoschanz/drawing/blob/master/LICENSE

import cairo
from .abstract_eraser import AbstractEraser

class EraserColor(AbstractEraser):
	__gtype_name__ = 'EraserColor'

	def __init__(self, **kwargs):
		super().__init__()

	############################################################################
################################################################################

