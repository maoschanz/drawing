# Licensed under GPL3 https://github.com/maoschanz/drawing/blob/master/LICENSE

import cairo
from .abstract_eraser import AbstractEraser

class EraserRubber(AbstractEraser):
	__gtype_name__ = 'EraserRubber'

	def __init__(self):
		super().__init__()

	def get_label_options(self, options={}):
		label_options = _("Pencil") # XXX << pas ultra clair/adapté en vrai
		label_options += " - " + {
			'alpha': _("Transparency"),
			'initial': _("Default color"),
			'secondary': _("Secondary color")
		}[options['selection-color']]
		return label_options

	def get_active_options(self, options={}):
		return ['selection-color']

	def on_release(self, cairo_context, press, event, path=None):
		if path is None:
			cairo_context.move_to(*press)
		else:
			cairo_context.append_path(path)
		cairo_context.line_to(*event)
		return cairo_context.copy_path()

	############################################################################

	def do_operation(self, cairo_context, operation):
		cairo_context.set_operator(cairo.Operator.SOURCE)
		cairo_context.set_source_rgba(*operation['replacement'])
		cairo_context.set_line_cap(cairo.LineCap.ROUND)
		cairo_context.set_line_join(cairo.LineJoin.ROUND)
		cairo_context.set_line_width(operation['line_width'])
		cairo_context.append_path(operation['path'])
		cairo_context.stroke()

	############################################################################
################################################################################

