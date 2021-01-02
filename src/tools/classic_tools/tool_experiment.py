# tool_experiment.py

import cairo, math
from gi.repository import Gdk
from .abstract_classic_tool import AbstractClassicTool
from .utilities_paths import utilities_smooth_path

class ToolExperiment(AbstractClassicTool):
	__gtype_name__ = 'ToolExperiment'

	def __init__(self, window, **kwargs):
		super().__init__('experiment', _("Experiment"), 'applications-utilities-symbolic', window)
		self.row.get_style_context().add_class('destructive-action')
		self._path = None

		# In order to draw pressure-sensitive lines, the path is collected as
		# an array whose elements are dicts (keys are 'x', 'y', 'p'). An actual
		# cairo path will be built from this data when necessary.
		self._manual_path = []

		self._use_antialias = True
		self._operators_dict = {
			'CLEAR': cairo.Operator.CLEAR,
			'SOURCE': cairo.Operator.SOURCE,
			'OVER': cairo.Operator.OVER,
			'IN': cairo.Operator.IN,
			'OUT': cairo.Operator.OUT,
			'ATOP': cairo.Operator.ATOP,
			'DEST': cairo.Operator.DEST,
			'DEST_OVER': cairo.Operator.DEST_OVER,
			'DEST_IN': cairo.Operator.DEST_IN,
			'DEST_OUT': cairo.Operator.DEST_OUT,
			'DEST_ATOP': cairo.Operator.DEST_ATOP,
			'XOR': cairo.Operator.XOR,
			'ADD': cairo.Operator.ADD,
			'SATURATE': cairo.Operator.SATURATE,
			'MULTIPLY': cairo.Operator.MULTIPLY,
			'SCREEN': cairo.Operator.SCREEN,
			'OVERLAY': cairo.Operator.OVERLAY,
			'DARKEN': cairo.Operator.DARKEN,
			'LIGHTEN': cairo.Operator.LIGHTEN,
			'COLOR_DODGE': cairo.Operator.COLOR_DODGE,
			'COLOR_BURN': cairo.Operator.COLOR_BURN,
			'HARD_LIGHT': cairo.Operator.HARD_LIGHT,
			'SOFT_LIGHT': cairo.Operator.SOFT_LIGHT,
			'DIFFERENCE': cairo.Operator.DIFFERENCE,
			'EXCLUSION': cairo.Operator.EXCLUSION,
			'HSL_HUE': cairo.Operator.HSL_HUE,
			'HSL_SATURATION': cairo.Operator.HSL_SATURATION,
			'HSL_COLOR': cairo.Operator.HSL_COLOR,
			'HSL_LUMINOSITY': cairo.Operator.HSL_LUMINOSITY
		}
		self._operator_label = "OVER"
		self.operator2 = cairo.Operator.OVER
		self._selected_mode = 'pressure'

		self.add_tool_action_enum('experiment_operator', self._operator_label)
		self.add_tool_action_enum('experiment_mode', self._selected_mode)

	def get_edition_status(self):
		return "You're not supposed to use this tool (development only)."

	def get_options_label(self):
		self._set_active_operator()
		self._set_active_mode()
		if self._selected_mode == 'simple':
			return self._operator_label
		else:
			return self._selected_mode

	############################################################################

	def _set_active_mode(self, *args):
		state_as_string = self.get_option_value('experiment_mode')
		self._selected_mode = state_as_string

	def _set_active_operator(self, *args):
		state_as_string = self.get_option_value('experiment_operator')
		self.operator2 = self._operators_dict[state_as_string]
		self._operator_label = state_as_string

	############################################################################

	def on_press_on_area(self, event, surface, event_x, event_y):
		self._set_active_operator()
		self._set_active_mode()
		self.x_press = event_x
		self.y_press = event_y
		self.set_common_values(event.button, event_x, event_y)
		self._path = None
		self._manual_path = []
		self._add_pressured_point(event_x, event_y, event)

	def on_motion_on_area(self, event, surface, event_x, event_y):
		self._add_point(event_x, event_y)
		self._add_pressured_point(event_x, event_y, event)
		operation = self.build_operation()
		self.do_tool_operation(operation)

	def on_release_on_area(self, event, surface, event_x, event_y):
		self._add_point(event_x, event_y)
		self._add_pressured_point(event_x, event_y, event)
		operation = self.build_operation()
		operation['is_preview'] = False
		# TODO dans un monde parfait c'est là qu'on smooth le path je pense
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
		source = device.get_source()
		# print(source) # TODO ça peut être Gdk.InputSource.MOUSE, ou .TOUCHPAD,
		# ou bien des trucs pertinents comme Gdk.InputSource.ERASER ou .PEN
		# J'ignore s'il faut faire quelque chose de cette information ? Il y a
		# ptêt des touchpads ou des touchscreens sensibles à la pression non ?

		tool = event.get_device_tool()
		# print(tool) # TODO ça indique qu'on a ici un appareil dédié au dessin
		# (vaut `None` si c'est pas le cas). Autrement on peut avoir des valeurs
		# comme Gdk.DeviceToolType.PEN, .ERASER, .BRUSH, .PENCIL, ou .AIRBRUSH,
		# et aussi (même si jsuis pas sûr ce soit pertinent) .UNKNOWN, .MOUSE et
		# .LENS (fuck ces bourgeois avec des tablettes haut de gamme au pire).
		# On pourrait adapter le comportement (couleur/opérateur/aliasing/etc.)
		# à cette information à l'avenir.

		pressure = event.get_axis(Gdk.AxisUse.PRESSURE)
		# print(pressure)
		if pressure is None:
			return None
		return pressure

	def _add_point(self, event_x, event_y):
		cairo_context = self.get_context()
		if self._path is None:
			cairo_context.move_to(self.x_press, self.y_press)
		else:
			cairo_context.append_path(self._path)
		cairo_context.line_to(event_x, event_y)
		self._path = cairo_context.copy_path()

	############################################################################

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'rgba': self.main_color,
			'operator': self.operator2,
			'mode': self._selected_mode,
			'line_width': self.tool_width,
			'line_cap': cairo.LineCap.ROUND,
			'line_join': cairo.LineJoin.ROUND,
			'antialias': self._use_antialias,
			'is_preview': True,
			'path': self._path,
			'manual_path': self._manual_path
		}
		return operation

	def do_tool_operation(self, operation):
		if operation['path'] is None:
			return
		cairo_context = self.start_tool_operation(operation)
		cairo_context.set_line_cap(operation['line_cap'])
		cairo_context.set_line_join(operation['line_join'])
		rgba = operation['rgba']
		cairo_context.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)

		if operation['is_preview']:
			self.op_simple(operation, cairo_context)
			return # Previewing helps performance and debug
		if operation['mode'] == 'dynamic1':
			self.op_dynamic1_segments(operation, cairo_context)
		elif operation['mode'] == 'dynamic2':
			self.op_dynamic2_superposition(operation, cairo_context)
		elif operation['mode'] == 'dynamic3':
			self.op_dynamic3_mask(operation, cairo_context) # TODO
		elif operation['mode'] == 'pressure':
			self.op_pressure(operation, cairo_context)
		elif operation['mode'] == 'smooth':
			# self.op_simple(operation, cairo_context)
			self.op_smooth(operation, cairo_context)
		else:
			self.op_simple(operation, cairo_context)

	############################################################################

	def op_simple(self, operation, cairo_context):
		cairo_context.set_operator(operation['operator'])
		cairo_context.set_line_width(operation['line_width'])
		cairo_context.append_path(operation['path'])
		cairo_context.stroke()

	def op_smooth(self, operation, cairo_context):
		cairo_context.set_operator(cairo.Operator.OVER)
		cairo_context.set_line_width(operation['line_width'])
		utilities_smooth_path(cairo_context, operation['path'])
		cairo_context.stroke()

	############################################################################

	def op_dynamic1_segments(self, operation, cairo_context):
		"""Brush with speed-sensitive dynamic width, where the variation of
		width is drawn by a succession of segments. The first segment is shit,
		and it looks awful with semi-transparent colors."""

		# mask intersections between segments when semi-transparency
		cairo_context.set_operator(cairo.Operator.SOURCE)

		SMOOTH = True
		if SMOOTH:
			utilities_smooth_path(cairo_context, operation['path'])
			path = cairo_context.copy_path()
		else:
			path = operation['path']
		line_width = 0
		cairo_context.new_path()

		for pts in path:
			ok, future_x, future_y = self._future_point(pts)
			if not ok:
				continue
			current_x, current_y = cairo_context.get_current_point()
			dist = self._get_dist(current_x, current_y, future_x, future_y)
			new_width = 1 + int( operation['line_width']/max(1, 0.05 * dist) )
			if line_width == 0:
				line_width = new_width
			else:
				line_width = (new_width + line_width) / 2
			line_width = max(1, line_width)
			cairo_context.set_line_width(line_width)
			self._add_segment(cairo_context, pts)
			cairo_context.stroke()
			cairo_context.move_to(future_x, future_y)

	def op_dynamic2_superposition(self, operation, cairo_context):
		"""Brush with speed-sensitive dynamic width, where the variation of
		width is drawn by a superposition of segments. It doesn't really support
		semi-transparent colors."""

		# cairo_context.set_operator(operation['operator'])
		SMOOTH = True
		if SMOOTH:
			utilities_smooth_path(cairo_context, operation['path'])
			path = cairo_context.copy_path()
		else:
			path = operation['path']
		base_width = operation['line_width']
		line_width = 0
		cairo_context.new_path()

		length = 1
		for pts in path:
			length += 1
		widths = [base_width] * length

		# Initializing widths (XXX faisable sans cairo_context) + factorisable
		# TODO pas correct, la width a un "retard" sur la vitesse du tracé
		i = 0
		for pts in path:
			i += 1
			ok, future_x, future_y = self._future_point(pts)
			if not ok:
				continue
			current_x, current_y = cairo_context.get_current_point()
			dist = self._get_dist(current_x, current_y, future_x, future_y)
			new_width = 1 + int(base_width / max(1, 0.05 * dist))
			if line_width == 0:
				line_width = (new_width + base_width) / 2
			else:
				line_width = (new_width + line_width + line_width) / 3
			widths[i] = max(1, int(line_width))
			cairo_context.move_to(future_x, future_y)

		# For each possible width, draw some portions of the path
		line_width = base_width
		cairo_context.new_path()
		while line_width > 1:
			cairo_context.set_line_width(line_width)
			to_draw = [True] * length
			for i in range(length):
				to_draw[i] = widths[i] >= line_width
			empty = True
			i = 0
			for pts in path:
				i += 1
				ok, future_x, future_y = self._future_point(pts)
				if not ok:
					# print("not ok", i)
					continue
				current_x, current_y = cairo_context.get_current_point()
				if to_draw[i]:
					empty = False
					# print("draw", i, "with width", line_width)
					self._add_segment(cairo_context, pts)
				else:
					if not empty:
						cairo_context.stroke()
						empty = True
				cairo_context.move_to(future_x, future_y)
			cairo_context.stroke()
			cairo_context.new_path()
			line_width = max(line_width - 1, 1)
		# Would be needed if the while loop was less exhaustive
		# cairo_context.set_line_width(line_width)
		# cairo_context.append_path(path)
		# cairo_context.stroke()

	def op_dynamic3_mask(self, operation, cairo_context):
		pass
		# TODO support operators and semi-transparency, using tricks like what
		# the dest_in operator is doing to blur. Same superposition as dynamic2

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
		# -> mieux factorisable !
		"""..."""

		# 1. construction d'un path et initialisation d'un array de width
		line_width = operation['line_width']
		widths = []
		dists = []
		cairo_context.new_path()
		p2 = None
		for pt in operation['manual_path']:
			cairo_context.line_to(pt['x'], pt['y'])
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
					# width of "100%" of operation['line_width'], so "* 2"
					widths.append(line_width * seg_width * 2)
			p2 = pt

		# If nothing in widths, it has to be filled from dists
		if len(widths) == 0:
			min_dist = min(dists)
			max_dist = max(dists)
			for dist in dists:
				width = line_width # TODO
				widths.append(width)

		raw_path = cairo_context.copy_path()

		# 2. smoothing du path
		cairo_context.new_path()
		utilities_smooth_path(cairo_context, raw_path)
		smoothed_path = cairo_context.copy_path()

		# 3. création d'un contexte d'une surface vierge
		# TODO

		# 4. parcours du path : dessin manuel (op source) avec widths associées
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

		# 5. painting sur la vraie surface selon l'opérateur choisi
		# TODO

	############################################################################
################################################################################

