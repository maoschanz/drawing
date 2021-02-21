# Licensed under GPL3 https://github.com/maoschanz/drawing/blob/master/LICENSE

import cairo, math
from gi.repository import Gdk
from .abstract_brush import AbstractBrush
from .utilities_paths import utilities_smooth_path

class BrushSimple(AbstractBrush):
	__gtype_name__ = 'BrushSimple'

	def draw_preview(self, operation, cairo_context):
		cairo_context.set_line_cap(cairo.LineCap.ROUND)
		cairo_context.set_line_join(cairo.LineJoin.ROUND)
		rgba = operation['rgba']
		cairo_context.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)
		super().draw_preview(operation, cairo_context)

	############################################################################

	def do_brush_operation(self, cairo_context, operation):
		"""Brush with dynamic width, where the variation of width is drawn by a
		succession of segments. If pressure is detected, the width is pressure-
		sensitive, otherwise it's speed-sensitive (with a heavy ponderation to
		make it less ugly)."""

		if operation['is_preview']: # Previewing helps performance & debug
			operation['line_width'] = int(operation['line_width'] / 2)
			return self.draw_preview(operation, cairo_context)

		if len(operation['path']) < 3:
			# XXX minimum 3 points to get minimum 2 segments to avoid "list
			# index out of range" errors when running the for loops
			return

		self.operation_on_mask(operation, cairo_context)

	def do_masked_brush_op(self, cairo_context, operation):
		cairo_context.set_line_cap(cairo.LineCap.ROUND)
		cairo_context.set_line_join(cairo.LineJoin.ROUND)

		# Build a raw path with lines between the points
		cairo_context.new_path()
		for pt in operation['path']:
			cairo_context.line_to(pt['x'], pt['y'])
		raw_path = cairo_context.copy_path()

		# Smooth this raw path
		cairo_context.new_path()
		utilities_smooth_path(cairo_context, raw_path)
		smoothed_path = cairo_context.copy_path()

		# Build an array with all the widths for each segment
		widths = self._build_widths(operation['path'], operation['line_width'])

		# Run through the path to manually draw each segment with its width
		i = 0
		cairo_context.new_path()
		for segment in smoothed_path:
			i = i + 1
			ok, future_x, future_y = self._future_point(segment)
			if not ok:
				cairo_context.move_to(future_x, future_y)
				continue
			current_x, current_y = cairo_context.get_current_point()
			cairo_context.set_line_width(widths[i - 1])
			self._add_segment(cairo_context, segment)
			cairo_context.stroke()
			cairo_context.move_to(future_x, future_y)

	############################################################################
	# Private methods ##########################################################

	def _build_widths(self, manual_path, base_width):
		"""Build an array of widths from the raw data, either using the value of
		the pressure or based on the estimated speed of the movement."""
		widths = []
		dists = []
		p2 = None
		for pt in manual_path:
			if pt['p'] is None:
				# No data about pressure
				if p2 is not None:
					dists.append(self._get_dist(pt['x'], pt['y'], p2['x'], p2['y']))
			else:
				# There are data about pressure
				if p2 is not None:
					if p2['p'] == 0 or pt['p'] == 0:
						seg_width = 0
					else:
						seg_width = (p2['p'] + pt['p']) / 2
					# A segment whose 2 points have a 50% pressure shall have a
					# width of "100%" of the base_width, so "base * mean * 2"
					widths.append(base_width * seg_width * 2)
			p2 = pt

		# If nothing in widths, it has to be filled from dists
		if len(widths) == 0:
			min_dist = min(dists)
			max_dist = max(dists)
			temp_width = 0
			for dist in dists:
				new_width = 1 + int(base_width / max(1, 0.05 * dist))
				if temp_width == 0:
					temp_width = (new_width + base_width) / 2
				else:
					temp_width = (new_width + temp_width + temp_width) / 3
				width = max(1, int(temp_width))
				widths.append(width)

		return widths

	def _add_segment(self, cairo_context, pts):
		if pts[0] == cairo.PathDataType.CURVE_TO:
			cairo_context.curve_to(pts[1][0], pts[1][1], pts[1][2], pts[1][3], \
			                                             pts[1][4], pts[1][5])
		elif pts[0] == cairo.PathDataType.LINE_TO:
			cairo_context.line_to(pts[1][0], pts[1][1])

	def _future_point(self, pts):
		if pts[0] == cairo.PathDataType.CURVE_TO:
			return True, pts[1][4], pts[1][5]
		elif pts[0] == cairo.PathDataType.LINE_TO:
			return True, pts[1][0], pts[1][1]
		else: # all paths start with a cairo.PathDataType.MOVE_TO
			return False, pts[1][0], pts[1][1]

	def _get_dist(self, x1, y1, x2, y2):
		dist2 = (x1 - x2) * (x1 - x2) + (y1 - y2) * (y1 - y2)
		return math.sqrt(dist2)

	############################################################################
################################################################################

