
# tool_brush.py
#
# Copyright 2018-2021 Romain F. T.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import cairo, math
from gi.repository import Gdk
from .abstract_classic_tool import AbstractClassicTool
from .utilities_paths import utilities_smooth_path

class ToolBrush(AbstractClassicTool):
	__gtype_name__ = 'ToolBrush'

	def __init__(self, window, **kwargs):
		super().__init__('brush', _("Brush"), 'tool-brush-symbolic', window)
		self.use_operator = True
		self._last_use_pressure = False
		self.row.get_style_context().add_class('destructive-action')

	# TODO options potentielles : des brosses différentes ? l'antialiasing ?

	def get_options_model(self):
		return None

	def get_options_label(self):
		return _("No options")

	def get_edition_status(self):
		label = self.label + ' - '
		if self._last_use_pressure:
			label = label + _("Width depends on the stylus pressure")
		else:
			label = label + _("Width depends on the mouse speed")
		return label

	############################################################################

	def on_press_on_area(self, event, surface, event_x, event_y):
		self.set_common_values(event.button, event_x, event_y)
		self._manual_path = []
		self._add_pressured_point(event_x, event_y, event)
		self._last_use_pressure = self._manual_path[0]['p'] is not None

	def on_motion_on_area(self, event, surface, event_x, event_y):
		self._add_pressured_point(event_x, event_y, event)
		operation = self.build_operation()
		self.do_tool_operation(operation)

	def on_release_on_area(self, event, surface, event_x, event_y):
		self._add_pressured_point(event_x, event_y, event)
		operation = self.build_operation()
		operation['is_preview'] = False
		self.apply_operation(operation)

	############################################################################

	def _add_pressured_point(self, event_x, event_y, event):
		new_point = {
			'x': event_x,
			'y': event_y,
			'p': self._get_pressure(event)
		}
		self._manual_path.append(new_point)

	def _get_pressure(self, event):
		device = event.get_source_device()
		# print(device)
		if device is None:
			return None
		# source = device.get_source()
		# print(source) # J'ignore s'il faut faire quelque chose de cette info

		tool = event.get_device_tool()
		# print(tool) # ça indique qu'on a ici un appareil dédié au dessin (vaut
		# `None` si c'est pas le cas). Autrement on peut avoir des valeurs comme
		# Gdk.DeviceToolType.PEN, .ERASER, .BRUSH, .PENCIL, ou .AIRBRUSH, et
		# aussi (même si jsuis pas sûr ce soit pertinent) .UNKNOWN, .MOUSE et
		# .LENS, on pourrait adapter le comportement (couleur/opérateur/etc.)
		# à cette information à l'avenir.

		pressure = event.get_axis(Gdk.AxisUse.PRESSURE)
		# print(pressure)
		if pressure is None:
			return None
		return pressure

	############################################################################

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'rgba': self.main_color,
			'operator': self._operator,
			'line_width': self.tool_width,
			'antialias': self._use_antialias,
			'is_preview': True,
			'path': self._manual_path
		}
		return operation

	def do_tool_operation(self, operation):
		if operation['path'] is None or len(operation['path']) < 1:
			return
		cairo_context = self.start_tool_operation(operation)
		cairo_context.set_line_cap(cairo.LineCap.ROUND)
		cairo_context.set_line_join(cairo.LineJoin.ROUND)
		rgba = operation['rgba']
		cairo_context.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)

		if operation['is_preview']: # Previewing helps performance & debug
			operation['line_width'] = int(operation['line_width'] / 2)
			return self.op_simple(operation, cairo_context)
		self.op_pressure(operation, cairo_context)

	############################################################################

	def op_simple(self, operation, cairo_context):
		cairo_context.set_operator(operation['operator'])
		cairo_context.set_line_width(operation['line_width'])
		cairo_context.new_path()
		for pt in operation['path']:
			cairo_context.line_to(pt['x'], pt['y'])
		cairo_context.stroke()

	############################################################################

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

	def op_pressure(self, operation, cairo_context):
		"""Brush with dynamic width, where the variation of width is drawn by a
		succession of segments. If pressure is detected, the width is pressure-
		sensitive, otherwise it's speed-sensitive (with a heavy ponderation to
		make it less ugly)."""

		if len(operation['path']) < 3:
			# XXX minimum 3 points to get minimum 2 segments to avoid "list
			# index out of range" errors when running the for loops
			return

		# Build an array with all the widths for each segment
		widths = self._build_widths(operation['path'], operation['line_width'])

		# Build a raw path with lines between the points
		cairo_context.new_path()
		for pt in operation['path']:
			cairo_context.line_to(pt['x'], pt['y'])
		raw_path = cairo_context.copy_path()

		# Smooth this raw path
		cairo_context.new_path()
		utilities_smooth_path(cairo_context, raw_path)
		smoothed_path = cairo_context.copy_path()

		# Creation of a blank surface with a new context using the options set
		# by the user, except the operator.
		w = self.get_surface().get_width()
		h = self.get_surface().get_height()
		mask = cairo.ImageSurface(cairo.Format.ARGB32, w, h)
		context2 = cairo.Context(mask)
		context2.set_line_cap(cairo.LineCap.ROUND)
		context2.set_line_join(cairo.LineJoin.ROUND)
		rgba = operation['rgba']
		context2.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)

		# Run through the path to manually draw each segment with its width
		context2.set_operator(cairo.Operator.SOURCE)
		i = 0
		context2.new_path()
		for segment in smoothed_path:
			i = i + 1
			ok, future_x, future_y = self._future_point(segment)
			if not ok:
				context2.move_to(future_x, future_y)
				continue
			current_x, current_y = context2.get_current_point()
			context2.set_line_width(widths[i - 1])
			self._add_segment(context2, segment)
			context2.stroke()
			context2.move_to(future_x, future_y)

		# Paint the surface onto the actual image with the chosen operator
		cairo_context.set_operator(operation['operator']) # TODO but the blur?
		cairo_context.set_source_surface(mask)
		cairo_context.paint()

	############################################################################
################################################################################

