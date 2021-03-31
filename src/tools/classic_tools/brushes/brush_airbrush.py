# Licensed under GPL3 https://github.com/maoschanz/drawing/blob/master/LICENSE

import cairo, random
from .abstract_brush import AbstractBrush

class BrushAirbrush(AbstractBrush):
	__gtype_name__ = 'BrushAirbrush'

	def _get_status(self, use_pressure):
		label = _("Airbrush") + " - "
		if use_pressure:
			label += _("Density depends on the stylus pressure")
		else:
			label += _("Density depends on the mouse speed")
		return label

	def do_brush_operation(self, cairo_context, operation):
		"""Airbrush whose radius is the line width. The density of droplets is
		related to the stylus pressure."""

		cairo_context.set_operator(operation['operator'])
		rgba = operation['rgba']
		cairo_context.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)

		# if operation['is_preview']: # Previewing helps performance & debug
		# 	operation['line_width'] = int(operation['line_width'] / 2)
		# 	return self.draw_preview(operation, cairo_context)

		cairo_context.set_line_width(1)
		random.seed(1) # this hardcoded seed avoids the droplets changing their
		# positions when the user undoes an following operation
		half_width = operation['line_width'] / 2
		droplets = 20 # could be like 15 + log(width) maybe?

		for pt in operation['path']:
			if pt['p'] is not None:
				droplets = int(40 * pt['p'])
			for i in range(droplets):
				cairo_context.new_path()
				x = pt['x'] + random.randint(-1 * half_width, half_width)
				y = pt['y'] + random.randint(-1 * half_width, half_width)
				cairo_context.move_to(x, y)
				cairo_context.rel_line_to(1, 1)
				cairo_context.stroke()
		# XXX the pattern is square, not round

	############################################################################
################################################################################

