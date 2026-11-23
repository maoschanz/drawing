# Licensed under GPL3 https://github.com/maoschanz/drawing/blob/master/LICENSE

import cairo, math
from gi.repository import Gdk

################################################################################

def utilities_get_rgba_for_xy(surface, x, y):
	# Guard clause: we can't perform color picking outside of the surface
	if x < 0 or x > surface.get_width() or y < 0 or y > surface.get_height():
		return None
	screenshot = Gdk.pixbuf_get_from_surface(surface, float(x), float(y), 1, 1)
	rgba_vals = screenshot.get_pixels()
	return rgba_vals

def utilities_get_magic_path(surface, x, y):
	"""Return the pixel-edge outline of the clicked four-connected RGBA region.

	A single snapshot avoids allocating a pixbuf for every examined pixel.
	Each scanline span is visited once; boundary edges are consumed once when
	building the path. Neither search depends on finding an approximate edge.
	"""
	width, height = surface.get_width(), surface.get_height()
	if x < 0 or y < 0 or x >= width or y >= height:
		return None
	x, y = int(x), int(y)
	pixbuf = Gdk.pixbuf_get_from_surface(surface, 0, 0, width, height)
	if not pixbuf.get_has_alpha():
		pixbuf = pixbuf.add_alpha(False, 0, 0, 0)
	pixels = memoryview(pixbuf.get_pixels()).cast('I')
	stride = pixbuf.get_rowstride() // 4
	color = pixels[y * stride + x]
	visited = bytearray(width * height)
	pending = [(x, y)]
	spans = []

	while pending:
		x, y = pending.pop()
		row, pixel_row = y * width, y * stride
		if visited[row + x]:
			continue
		left = right = x
		while left > 0 and not visited[row + left - 1] \
		and pixels[pixel_row + left - 1] == color:
			left -= 1
		while right + 1 < width and not visited[row + right + 1] \
		and pixels[pixel_row + right + 1] == color:
			right += 1
		right += 1
		visited[row + left:row + right] = b'\x01' * (right - left)
		spans.append((y, left, right))
		for neighbor in (y - 1, y + 1):
			if neighbor < 0 or neighbor >= height:
				continue
			x = left
			while x < right:
				if not visited[neighbor * width + x] \
				and pixels[neighbor * stride + x] == color:
					pending.append((x, neighbor))
					x += 1
					while x < right and not visited[neighbor * width + x] \
					and pixels[neighbor * stride + x] == color:
						x += 1
				else:
					x += 1

	# Only emit the perimeter: row rectangles would leave internal seams in
	# the color-selection outline. Clockwise edges keep the region on the
	# right, giving holes the opposite winding without a special fill rule.
	edges = {}
	def add_edge(start, end):
		edges.setdefault(start, []).append(end)

	for y, left, right in spans:
		add_edge((left, y + 1), (left, y))
		add_edge((right, y), (right, y + 1))
		for neighbor, edge_y in ((y - 1, y), (y + 1, y + 1)):
			x = left
			while x < right:
				if 0 <= neighbor < height:
					row = neighbor * width
					start = visited.find(0, row + x, row + right)
					if start == -1:
						break
					x = start - row
					end = visited.find(1, start, row + right)
					end = right if end == -1 else end - row
				else:
					end = right
				if neighbor < y:
					add_edge((x, edge_y), (end, edge_y))
				else:
					add_edge((end, edge_y), (x, edge_y))
				x = end

	context = cairo.Context(surface)
	# Keep one list of starting vertices. Repeatedly restarting a dictionary
	# iterator after deleting a loop rescans its deleted slots for every hole.
	for start in list(edges):
		while start in edges:
			current = start
			context.move_to(*start)
			direction = None
			while True:
				ends = edges[current]
				# Turn right at diagonal contacts to keep the boundaries
				# separate instead of making a self-crossing outline.
				if direction is None or len(ends) == 1:
					end = ends.pop()
				else:
					end = min(ends, key=lambda point:
						(_path_direction(current, point) - direction - 1) % 4)
					ends.remove(end)
				if not ends:
					del edges[current]
				direction = _path_direction(current, end)
				context.line_to(*end)
				current = end
				if current == start:
					break
			context.close_path()
	return context.copy_path()

def _path_direction(start, end):
	if end[0] > start[0]:
		return 0
	if end[1] > start[1]:
		return 1
	if end[0] < start[0]:
		return 2
	return 3

################################################################################

# The coordinates of the corners of the triangle. These points are defined as if
# the end of the arrow line is at "0, 0" and rotated by 0 degrees.
ARROW_TRIANGLE = [
	(0.0, 0.0),
	(-2.747, 1.0),
	(-2.747, -1.0),
]

MIN_ARROW_SCALE = 3

def utilities_add_arrow_triangle(cairo_context, x2, y2, x1, y1, line_width):
	"""Adds a triangular head to the current path."""
	if x1 == x2 and y1 == y2:
		line_angle = 0
	else:
		line_angle = math.atan2(y2 - y1, x2 - x1)
	sin, cos = math.sin(line_angle), math.cos(line_angle)

	# FIXME cases with very short last segment
	# if scale == line_width, dashed arrow will look like shit
	scale = max(line_width * 1.1, MIN_ARROW_SCALE)

	# when the last segment of the line is very short, the head is scaled down
	# last_segment_length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
	# scale = min(scale, last_segment_length/line_width)
	# ^XXX broken with dashes
	# TODO ça peut ne plus être nécessaire si je décale la tête

	head = []
	# scale, rotate and translate the arrow triangle
	for x, y in ARROW_TRIANGLE:
		p = (x * scale, y * scale)
		p = (p[0] * cos - p[1] * sin, p[0] * sin + p[1] * cos)
		p = (p[0] + x2, p[1] + y2)
		head.append(p)

	# draw the arrow triangle
	_draw_head(cairo_context, head, True)

	# shameful hack to get a full head in cases where the line is dashed
	if cairo_context.get_dash_count() > 0:
		_draw_head(cairo_context, head, False)
		_draw_head(cairo_context, head, False)
		_draw_head(cairo_context, head, False)
		_draw_head(cairo_context, head, False)

	# XXX the path isn't filled because the path is opened by the first point of
	# the line/curve and it can't be closed so easily
	cairo_context.close_path()
	# The stroke must be done afterwards, by the calling method

def _draw_head(cairo_context, head, first_try):
	if first_try:
		cairo_context.move_to(*head[0])
	else:
		cairo_context.line_to(*head[0])
	cairo_context.line_to(*head[1])
	cairo_context.line_to(*head[2])

################################################################################
# Path smoothing ###############################################################

def utilities_smooth_path(cairo_context, cairo_path):
	"""Extrapolate a path made of straight lines into a path made of curves. New
	points are added according to the length of the line it replaces, the length
	of the previous one, and the length of the next one."""
	x1 = y1 = None
	x2 = y2 = None
	x3 = y3 = None
	x4 = y4 = None
	for pts in cairo_path:
		if pts[1] == ():
			continue
		x1, y1, x2, y2, x3, y3, x4, y4 = _next_arc(cairo_context, \
		                           x2, y2, x3, y3, x4, y4, pts[1][0], pts[1][1])
	_next_arc(cairo_context, x2, y2, x3, y3, x4, y4, None, None)
	# cairo_context.stroke()

def _next_point(x1, y1, x2, y2, dist):
	coef = 0.1
	dx = x2 - x1
	dy = y2 - y1
	angle = math.atan2(dy, dx)
	nx = x2 + math.cos(angle) * dist * coef
	ny = y2 + math.sin(angle) * dist * coef
	return nx, ny

def _next_arc(cairo_context, x1, y1, x2, y2, x3, y3, x4, y4):
	if x2 is None or x3 is None:
		# No drawing possible yet, just continue to the next point
		return x1, y1, x2, y2, x3, y3, x4, y4
	dist = math.sqrt( (x2 - x3) * (x2 - x3) + (y2 - y3) * (y2 - y3) )
	if x1 is None and x4 is None:
		cairo_context.move_to(x2, y2)
		cairo_context.line_to(x3, y3)
		return x1, y1, x2, y2, x3, y3, x4, y4
	elif x1 is None:
		nx1, ny1 = x2, y2
		nx2, ny2 = _next_point(x4, y4, x3, y3, dist)
	elif x4 is None:
		nx1, ny1 = _next_point(x1, y1, x2, y2, dist)
		nx2, ny2 = x3, y3
	else:
		nx1, ny1 = _next_point(x1, y1, x2, y2, dist)
		nx2, ny2 = _next_point(x4, y4, x3, y3, dist)
	cairo_context.curve_to(nx1, ny1, nx2, ny2, x3, y3)
	return x1, y1, x2, y2, x3, y3, x4, y4

################################################################################

