# Licensed under GPL3 https://github.com/maoschanz/drawing/blob/master/LICENSE

import cairo, random
from .abstract_brush import AbstractBrush

class BrushHairy(AbstractBrush):
	__gtype_name__ = 'BrushHairy'

	def _get_status(self, use_pressure, brush_direction):
		label = _("Hairy brush")
		if use_pressure:
			label += " - " + _("Width depends on the stylus pressure")
		return label

	def draw_preview(self, operation, cairo_context):
		cairo_context.set_line_cap(cairo.LineCap.ROUND)
		cairo_context.set_line_join(cairo.LineJoin.BEVEL)
		rgba = operation['rgba']
		cairo_context.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)
		super().draw_preview(operation, cairo_context)

	############################################################################

	def do_brush_operation(self, cairo_context, operation):
		"""Straight-shaped brush, like an orientable feather pen. The width is
		pressure-sensitive but otherwise it's NOT speed sensitive."""

		if operation['is_preview']: # Previewing helps performance & debug
			return self.draw_preview(operation, cairo_context)

		self.operation_on_mask(operation, cairo_context)

	def do_masked_brush_op(self, cairo_context, operation):
		cairo_context.set_line_cap(cairo.LineCap.ROUND)
		cairo_context.set_line_join(cairo.LineJoin.ROUND)
		cairo_context.set_line_width(1)

		line_width = int(operation['line_width'] / 2)

		matrix = []
		random.seed(1) # this hardcoded seed avoids the hairs changing their
		# positions when the user undoes an following operation
		for i in range(line_width * 2):
			matrix.append({
				'dx': random.randint(-1 * line_width, line_width),
				'dy': random.randint(-1 * line_width, line_width)
			})
			# TODO other kinds of loops to define the matrix?

		use_pressure = operation['path'][0]['p'] is not None
		pressure = 1
		for hair in matrix:
			cairo_context.new_path()
			for point in operation['path']:
				if use_pressure and point['p'] > 0:
					pressure = point['p'] * 2
				px = point['x'] + hair['dx'] * pressure
				py = point['y'] + hair['dy'] * pressure
				cairo_context.line_to(px, py)
			cairo_context.stroke()

	############################################################################
################################################################################

