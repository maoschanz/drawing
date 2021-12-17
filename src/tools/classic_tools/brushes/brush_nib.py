# Licensed under GPL3 https://github.com/maoschanz/drawing/blob/master/LICENSE

import cairo
from .abstract_brush import AbstractBrush

class BrushNib(AbstractBrush):
	__gtype_name__ = 'BrushNib'

	def _get_tips(self, use_pressure, brush_direction):
		label_width = _("Calligraphic nib") + " - "
		if use_pressure:
			label_width += _("Width depends on the stylus pressure")
		else:
			label_width += _("Width depends on the line orientation")
		return [label_width]

	def draw_preview(self, operation, cairo_context):
		cairo_context.set_line_cap(cairo.LineCap.BUTT)
		cairo_context.set_line_join(cairo.LineJoin.ROUND)
		cairo_context.set_source_rgba(*operation['rgba'])
		super().draw_preview(operation, cairo_context)

	############################################################################

	def do_brush_operation(self, cairo_context, operation):
		"""Straight-shaped brush, like an orientable feather pen. The width is
		pressure-sensitive but otherwise it's NOT speed sensitive."""

		if operation['is_preview']: # Previewing helps performance & debug
			return self.draw_preview(operation, cairo_context)

		self.operation_on_mask(operation, cairo_context)

	def do_masked_brush_op(self, cairo_context, operation):
		# cairo_context.set_line_cap(cairo.LineCap.BUTT)
		# cairo_context.set_line_join(cairo.LineJoin.BEVEL)
		# cairo_context.set_line_width(1)

		line_width = operation['line_width'] / 2
		two_ways_path = []

		if operation['nib_dir'] == 'left':
			feather_def = {'x': 1, 'y': 1}
		elif operation['nib_dir'] == 'horizontal':
			feather_def = {'x': 1, 'y': 0}
		elif operation['nib_dir'] == 'vertical':
			feather_def = {'x': 0, 'y': 1}
		else: # operation['nib_dir'] == 'right':
			feather_def = {'x': 1, 'y': -1}

		dx_base = feather_def['x'] * line_width
		dy_base = feather_def['y'] * line_width
		use_pressure = operation['path'][0]['p'] is not None
		if not use_pressure:
			dx1 = dx_base
			dy1 = dy_base
			dx2 = dx_base
			dy2 = dy_base

		former_point = None
		for current_point in operation['path']:
			if former_point is not None:
				if use_pressure:
					dx1 = dx_base * former_point['p']
					dy1 = dy_base * former_point['p']
					dx2 = dx_base * current_point['p']
					dy2 = dy_base * current_point['p']
				cairo_context.new_path()
				x = current_point['x'] + dx2
				y = current_point['y'] + dy2
				cairo_context.move_to(x, y)
				x = current_point['x'] + dx2 * -1
				y = current_point['y'] + dy2 * -1
				cairo_context.line_to(x, y)
				x = former_point['x'] + dx1 * -1
				y = former_point['y'] + dy1 * -1
				cairo_context.line_to(x, y)
				x = former_point['x'] + dx1
				y = former_point['y'] + dy1
				cairo_context.line_to(x, y)
				# cairo_context.stroke_preserve() # TODO trouver autre chose
				cairo_context.fill()
			former_point = current_point

	############################################################################
################################################################################

