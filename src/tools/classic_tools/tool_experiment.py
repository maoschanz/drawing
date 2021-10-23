# tool_experiment.py

import cairo, math, random
from gi.repository import Gdk
from .abstract_classic_tool import AbstractClassicTool
from .utilities_paths import utilities_smooth_path

class ToolExperiment(AbstractClassicTool):
	__gtype_name__ = 'ToolExperiment'

	def __init__(self, window, **kwargs):
		super().__init__('experiment', _("Experiment"), 'applications-utilities-symbolic', window)

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
		self._selected_mode = 'feather'
		self._feather_dir = 'up'

		self.add_tool_action_enum('experiment_operator', self._operator_label)
		self.add_tool_action_enum('experiment_mode', self._selected_mode)

	def build_row(self):
		super().build_row()
		self.row.get_style_context().add_class('destructive-action')
		return self.row

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
		self.get_options_label()
		self.x_press = event_x
		self.y_press = event_y
		self.set_common_values(event.button, event_x, event_y)
		self._manual_path = []
		self._add_pressured_point(event_x, event_y, event)

	def on_motion_on_area(self, event, surface, event_x, event_y, render=True):
		self._add_pressured_point(event_x, event_y, event)
		if render:
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
			'path': self._manual_path
		}
		return operation

	def do_tool_operation(self, operation):
		if operation['path'] is None or len(operation['path']) < 1:
			return
		cairo_context = self.start_tool_operation(operation)
		cairo_context.set_line_cap(operation['line_cap'])
		cairo_context.set_line_join(operation['line_join'])
		rgba = operation['rgba']
		cairo_context.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)

		if operation['mode'] == 'pressure':
			if operation['is_preview']: # Previewing helps performance & debug
				operation['line_width'] = int(operation['line_width'] / 2)
				return self.op_simple(operation, cairo_context)
			self.op_pressure(operation, cairo_context)
		elif operation['mode'] == 'smooth':
			if operation['is_preview']: # Previewing helps performance & debug
				return self.op_simple(operation, cairo_context)
			self.op_smooth(operation, cairo_context)
		elif operation['mode'] == 'macro-w':
			self.op_macro_w(operation, cairo_context)
		else:
			self.op_simple(operation, cairo_context)

	############################################################################

	def op_macro_w(self, operation, cairo_context):
		"""Trying to study whatever tf is the rendering issue #337"""
		cairo_context.set_antialias(cairo.Antialias.DEFAULT)
		cairo_context.set_operator(cairo.Operator.HSL_HUE)
		cairo_context.set_line_width(operation['line_width'])
		cairo_context.new_path()
		cairo_context.line_to(50, 70)
		cairo_context.line_to(70, 50)
		cairo_context.line_to(90, 60)
		cairo_context.line_to(110, 85)
		cairo_context.line_to(130, 120)
		cairo_context.line_to(150, 110)
		cairo_context.line_to(170, 80)
		cairo_context.line_to(190, 50)
		cairo_context.line_to(210, 75)
		cairo_context.line_to(230, 90)
		cairo_context.line_to(250, 110)
		cairo_context.line_to(270, 70)
		cairo_context.line_to(290, 50)
		cairo_context.line_to(310, 75)
		cairo_context.line_to(330, 90)
		cairo_context.stroke()

	############################################################################

	def op_simple(self, operation, cairo_context):
		cairo_context.set_operator(operation['operator'])
		cairo_context.set_line_width(operation['line_width'])
		cairo_context.new_path()
		for pt in operation['path']:
			cairo_context.line_to(pt['x'], pt['y'])
		cairo_context.stroke()

	def op_smooth(self, operation, cairo_context):
		cairo_context.set_operator(cairo.Operator.OVER)
		cairo_context.set_line_width(operation['line_width'])

		# Build a cairo path from the raw data
		cairo_context.new_path()
		for pt in operation['path']:
			cairo_context.line_to(pt['x'], pt['y'])
		path = cairo_context.copy_path()

		# Smooth it
		cairo_context.new_path()
		utilities_smooth_path(cairo_context, path)

		# Draw it
		cairo_context.stroke()

	############################################################################
################################################################################

