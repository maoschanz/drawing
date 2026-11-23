#!/usr/bin/env python3

import gettext
import importlib
from pathlib import Path
import signal
import sys
import types
import unittest
from collections import deque
from unittest.mock import Mock

import cairo
import gi

gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')

# Meson installs these modules together, flattening the source directories.
source_dir = Path(__file__).resolve().parents[1] / 'src'
package = types.ModuleType('drawing')
package.__path__ = [str(source_dir)] + sorted({
	str(path.parent) for path in source_dir.rglob('*.py')
})
sys.modules['drawing'] = package
gettext.install('drawing')
paths = importlib.import_module('drawing.utilities_paths')
paint = importlib.import_module('drawing.tool_paint')
select = importlib.import_module('drawing.select_color')


def connected_region(grid, seed):
	# Deliberately use a pixel queue, independently of the scanline search.
	x, y = seed
	color = grid[y][x]
	region = {seed}
	pending = deque([seed])
	while pending:
		x, y = pending.popleft()
		for point in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
			x2, y2 = point
			if 0 <= y2 < len(grid) and 0 <= x2 < len(grid[0]) \
			and point not in region and grid[y2][x2] == color:
				region.add(point)
				pending.append(point)
	return region


def make_surface(grid, colors=None, surface_format=cairo.FORMAT_ARGB32):
	if colors is None:
		colors = [(1, 1, 1, 1), (0, 0, 0, 1)]
	surface = cairo.ImageSurface(surface_format, len(grid[0]), len(grid))
	context = cairo.Context(surface)
	context.set_operator(cairo.Operator.SOURCE)
	for y, row in enumerate(grid):
		for x, value in enumerate(row):
			context.set_source_rgba(*colors[value])
			context.rectangle(x, y, 1, 1)
			context.fill()
	return surface


def path_edges(path):
	edges = set()
	start = current = None
	for kind, coords in path:
		if kind == cairo.PATH_MOVE_TO:
			start = current = tuple(map(int, coords))
		elif kind in (cairo.PATH_LINE_TO, cairo.PATH_CLOSE_PATH):
			end = start if kind == cairo.PATH_CLOSE_PATH else \
				tuple(map(int, coords))
			dx = (end[0] > current[0]) - (end[0] < current[0])
			dy = (end[1] > current[1]) - (end[1] < current[1])
			assert not (dx and dy), 'Non-axis-aligned boundary'
			while current != end:
				point = (current[0] + dx, current[1] + dy)
				assert (current, point) not in edges, 'Repeated boundary edge'
				edges.add((current, point))
				current = point
	return edges


def region_edges(region):
	edges = set()
	for x, y in region:
		for neighbor, start, end in (
			((x, y - 1), (x, y), (x + 1, y)),
			((x + 1, y), (x + 1, y), (x + 1, y + 1)),
			((x, y + 1), (x + 1, y + 1), (x, y + 1)),
			((x - 1, y), (x, y + 1), (x, y)),
		):
			if neighbor not in region:
				edges.add((start, end))
	return edges


class MagicPathTests(unittest.TestCase):

	def setUp(self):
		def timed_out(signum, frame):
			raise AssertionError('Region tracing did not terminate')
		self.previous_handler = signal.signal(signal.SIGALRM, timed_out)
		signal.setitimer(signal.ITIMER_REAL, 10)

	def tearDown(self):
		signal.setitimer(signal.ITIMER_REAL, 0)
		signal.signal(signal.SIGALRM, self.previous_handler)

	def assert_region(self, grid, seed, colors=None, **kwargs):
		surface = make_surface(grid, colors, **kwargs)
		before = bytes(surface.get_data())
		path = paths.utilities_get_magic_path(surface, *seed)
		self.assertIsNotNone(path)
		self.assertEqual(bytes(surface.get_data()), before)
		region = connected_region(grid, seed)
		self.assertEqual(path_edges(path), region_edges(region))
		context = cairo.Context(surface)
		context.append_path(path)
		for y, row in enumerate(grid):
			for x in range(len(row)):
				self.assertEqual(context.in_fill(x + 0.5, y + 0.5),
					(x, y) in region, (grid, seed, x, y))
		return surface, path, region

	def test_original_thin_boundary_reproducer(self):
		signal.setitimer(signal.ITIMER_REAL, 2)
		grid = [[int(y == 4) for x in range(12)] for y in range(12)]
		self.assert_region(grid, (6, 8))

	def test_exhaustive_three_by_three_masks(self):
		for bits in range(512):
			grid = [[(bits >> (y * 3 + x)) & 1 for x in range(3)]
				for y in range(3)]
			for y in range(3):
				for x in range(3):
					self.assert_region(grid, (x, y))

	def test_many_separate_holes(self):
		grid = [[int(x % 2 == 1 and y % 2 == 1)
			for x in range(128)] for y in range(80)]
		self.assert_region(grid, (0, 0))

	def test_holes_necks_and_diagonal_contacts(self):
		for rows in (
			['00000', '01110', '01010', '01110', '00000'],
			['00100', '00100', '00000', '00100', '00100'],
			['0000', '0100', '0010', '0000'],
			['10101', '00000', '10101'],
			['0'], ['00000'], ['0', '0', '0'],
		):
			grid = [list(map(int, row)) for row in rows]
			for y, row in enumerate(grid):
				for x in range(len(row)):
					self.assert_region(grid, (x, y))

	def test_alpha_and_rgb_surfaces(self):
		grid = [[0, 0, 1, 2], [0, 1, 1, 2], [0, 0, 2, 2]]
		colors = [(1, 0, 0, 0.5), (1, 0, 0, 1), (0, 0, 0, 0)]
		for seed in ((0, 0), (2, 0), (3, 0)):
			self.assert_region(grid, seed, colors)
		self.assert_region([[0, 1, 0], [0, 1, 1]], (0, 0),
			surface_format=cairo.FORMAT_RGB24)

	def test_bounds_and_fractional_coordinates(self):
		surface = make_surface([[0, 1], [1, 0]])
		for seed in ((-0.1, 0), (0, -0.1), (2, 0), (0, 2), (2, 2)):
			self.assertIsNone(paths.utilities_get_magic_path(surface, *seed))
		path = paths.utilities_get_magic_path(surface, 1.9, 1.9)
		self.assertEqual(path_edges(path), region_edges({(1, 1)}))

	def test_actual_paint_operations(self):
		grid = [[0, 0, 1, 0], [0, 1, 1, 0], [0, 0, 1, 0]]
		colors = [(1, 0, 0, 0.5), (0, 0, 1, 1)]
		for mode, operator, surface_format in (
			('fill', cairo.Operator.OVER, cairo.FORMAT_ARGB32),
			('replace', cairo.Operator.SOURCE, cairo.FORMAT_ARGB32),
			('fill', cairo.Operator.OVER, cairo.FORMAT_RGB24),
			('replace', cairo.Operator.SOURCE, cairo.FORMAT_RGB24),
		):
			for rgba in ((0, 1, 0, 1), (0, 1, 0, 0.5), (0, 0, 0, 0)):
				with self.subTest(mode=mode, rgba=rgba, format=surface_format):
					surface, path, region = self.assert_region(grid,
						(0, 0), colors, surface_format=surface_format)
					expected = make_surface(grid, colors, surface_format)
					context = cairo.Context(expected)
					context.set_operator(operator)
					context.set_source_rgba(*rgba)
					for x, y in region:
						context.rectangle(x, y, 1, 1)
					context.fill()
					tool = object.__new__(paint.ToolPaint)
					tool.get_context = lambda: cairo.Context(surface)
					getattr(tool, '_op_' + mode)({
						'path': path, 'new_rgba': rgba})
					self.assertEqual(bytes(surface.get_data()),
						bytes(expected.get_data()))

	def test_paint_callback_and_whole_image_mode(self):
		for mode in ('fill', 'replace', 'whole'):
			surface = make_surface([[0, 1], [0, 1]])
			tool = object.__new__(paint.ToolPaint)
			tool._magic_path = None
			tool.get_option_value = Mock(return_value=mode)
			tool.build_operation = Mock()
			tool.apply_operation = Mock()
			tool.on_release_on_area(None, surface, 0, 0)
			tool.apply_operation.assert_called_once_with(
				tool.build_operation.return_value)
			if mode != 'whole':
				self.assertEqual(path_edges(tool._magic_path),
					region_edges({(0, 0), (0, 1)}))

	def test_selection_callback_and_invalid_seed(self):
		surface = make_surface([[0, 1], [0, 1]])
		tool = object.__new__(select.ToolColorSelect)
		tool._pre_load_path = Mock()
		tool.build_operation = Mock()
		tool.apply_operation = Mock()
		tool.release_define(surface, 0, 0)
		self.assertEqual(path_edges(tool._pre_load_path.call_args[0][0]),
			region_edges({(0, 0), (0, 1)}))
		tool.apply_operation.assert_called_once()
		tool._pre_load_path.reset_mock()
		tool.apply_operation.reset_mock()
		tool.release_define(surface, 2, 0)
		tool._pre_load_path.assert_not_called()
		tool.apply_operation.assert_not_called()


if __name__ == '__main__':
	unittest.main()
