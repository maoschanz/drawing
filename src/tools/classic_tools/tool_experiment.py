# tool_experiment.py

import cairo, math

from .abstract_classic_tool import AbstractClassicTool
from .utilities_tools import utilities_smooth_path

class ToolExperiment(AbstractClassicTool):
	__gtype_name__ = 'ToolExperiment'

	def __init__(self, window, **kwargs):
		super().__init__('experiment', _("Experiment"), 'applications-utilities-symbolic', window)
		self.row.get_style_context().add_class('destructive-action')
		self._path = None

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
		self._operator_label = "DIFFERENCE"
		self._operator = cairo.Operator.DIFFERENCE
		self._selected_mode = 'dynamic2'

		self.add_tool_action_enum('experiment_operator', self._operator_label)
		self.add_tool_action_enum('experiment_mode', self._selected_mode)
		self.add_tool_action_simple('experiment_macro_scie', self._macro_scie)
		self.add_tool_action_boolean('experiment_antialias', self._use_antialias)

	def get_edition_status(self):
		return "You're not supposed to use this tool (development only)."

	def get_options_label(self):
		self._set_active_operator()
		self._set_active_mode()
		self._set_antialias()
		if self._selected_mode == 'simple':
			return self._operator_label
		else:
			return self._selected_mode

	############################################################################

	def _set_active_mode(self, *args):
		state_as_string = self.get_option_value('experiment_mode')
		self._selected_mode =  state_as_string

	def _set_antialias(self, *args):
		self._use_antialias = self.get_option_value('experiment_antialias')

	def _set_active_operator(self, *args):
		state_as_string = self.get_option_value('experiment_operator')
		self._operator = self._operators_dict[state_as_string]
		self._operator_label = state_as_string

	############################################################################

	def _macro_scie(self, *args):
		cairo_context = self.get_context()
		cairo_context.move_to(50, 50)
		cairo_context.line_to(100, 150)
		cairo_context.line_to(150, 50)
		cairo_context.line_to(200, 150)
		cairo_context.line_to(250, 50)
		cairo_context.line_to(300, 150)
		cairo_context.line_to(350, 50)
		cairo_context.line_to(375, 100)
		cairo_context.line_to(400, 50)
		cairo_context.line_to(425, 100)
		cairo_context.line_to(450, 50)
		cairo_context.line_to(500, 150)
		cairo_context.line_to(550, 50)
		self._path = cairo_context.copy_path()
		self._macros_common()

	def _macros_common(self):
		self.set_common_values(1)
		operation = self.build_operation()
		self.apply_operation(operation)

	############################################################################

	def on_press_on_area(self, event, surface, event_x, event_y):
		self._set_active_operator()
		self._set_active_mode()
		self._set_antialias()
		self.x_press = event_x
		self.y_press = event_y
		self.set_common_values(event.button)
		self._path = None

	def _add_point(self, event_x, event_y):
		cairo_context = self.get_context()
		if self._path is None:
			cairo_context.move_to(self.x_press, self.y_press)
		else:
			cairo_context.append_path(self._path)
		cairo_context.line_to(event_x, event_y)
		self._path = cairo_context.copy_path()

	def on_motion_on_area(self, event, surface, event_x, event_y):
		self._add_point(event_x, event_y)
		operation = self.build_operation()
		self.do_tool_operation(operation)

	def on_release_on_area(self, event, surface, event_x, event_y):
		self._add_point(event_x, event_y)
		operation = self.build_operation()
		operation['is_preview'] = False
		self.apply_operation(operation)

	############################################################################

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'rgba': self.main_color,
			'operator': self._operator,
			'mode': self._selected_mode,
			'line_width': self.tool_width,
			'line_cap': cairo.LineCap.ROUND,
			'line_join': cairo.LineJoin.ROUND,
			'antialias': self._use_antialias,
			'is_preview': True,
			'path': self._path
		}
		return operation

	def do_tool_operation(self, operation):
		self.start_tool_operation(operation)
		if operation['path'] is None:
			return
		cairo_context = self.get_context()
		cairo_context.set_line_cap(operation['line_cap'])
		cairo_context.set_line_join(operation['line_join'])
		rgba = operation['rgba']
		cairo_context.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)

		if operation['antialias']:
			cairo_context.set_antialias(cairo.Antialias.DEFAULT)
		else:
			cairo_context.set_antialias(cairo.Antialias.NONE)

		if operation['mode'] == 'dynamic':
			self.op_dynamic(operation, cairo_context)
		elif operation['mode'] == 'dynamic2':
			self.op_dynamic2(operation, cairo_context)
		elif operation['mode'] == 'juxta':
			self.op_juxta(operation, cairo_context)
		elif operation['mode'] == 'smooth':
			self.op_simple(operation, cairo_context)
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

	def op_juxta(self, operation, cairo_context):
		pass # TODO

	############################################################################

	def op_dynamic(self, operation, cairo_context):
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
			if pts[0] == cairo.PathDataType.CURVE_TO:
				future_x = pts[1][4]
				future_y = pts[1][5]
			elif pts[0] == cairo.PathDataType.LINE_TO:
				future_x = pts[1][0]
				future_y = pts[1][1]
			else:
				# all paths start with a cairo.PathDataType.MOVE_TO
				continue
			current_x, current_y = cairo_context.get_current_point()
			dist = math.sqrt( (current_x - future_x) * (current_x - future_x) \
			                 + (current_y - future_y) * (current_y - future_y) )
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

	def op_dynamic2(self, operation, cairo_context):
		# TODO idée d'amélioration : plutôþ que des booléens, stocker des
		# épaisseurs de trait, et les normaliser avant de tracer
		cairo_context.set_operator(cairo.Operator.OVER)
		line_width = operation['line_width']
		dist_max = 1
		SMOOTH = True
		if SMOOTH:
			utilities_smooth_path(cairo_context, operation['path'])
			path = cairo_context.copy_path()
		else:
			path = operation['path']

		length = 1
		for pts in path:
			length += 1
		drawn = [True] * length
		dist = 0

		while dist_max < 500:
			cairo_context.new_path()
			cairo_context.set_line_width(line_width)
			to_draw = [True] * length
			i = 0
			for pts in path:
				i += 1
				ok, future_x, future_y = self._future_point(pts)
				if not ok:
					continue
				current_x, current_y = cairo_context.get_current_point()
				dist = math.sqrt( (current_x - future_x) * (current_x - future_x) \
				             + (current_y - future_y) * (current_y - future_y) )
				if dist > dist_max:
					to_draw[i] = False
				cairo_context.move_to(future_x, future_y)

			if to_draw == drawn:
				dist_max = max(dist_max * 1.05, dist_max + 20)
				continue
			else:
				line_width = min(line_width - 1, line_width * 0.95)
				line_width = max(line_width, 1)

			cairo_context.new_path()
			empty = True
			i = 0
			for pts in path:
				i += 1
				ok, future_x, future_y = self._future_point(pts)
				if not ok:
					continue
				current_x, current_y = cairo_context.get_current_point()
				if to_draw[i]:
					empty = False
					self._add_segment(cairo_context, pts)
				else:
					if not empty:
						cairo_context.stroke()
						empty = True
				cairo_context.move_to(int(future_x), int(future_y))
			drawn = to_draw
			cairo_context.new_path()
		line_width = min(line_width - 1, line_width * 0.95)
		line_width = max(line_width, 1)
		cairo_context.set_line_width(line_width)
		cairo_context.append_path(path)
		cairo_context.stroke()
		# XXX ce qui marche presque, bien que très laid, le principal problème
		# est le dernier segment

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
			return False, 0, 0

	############################################################################
################################################################################

