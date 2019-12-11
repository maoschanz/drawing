# tool_shape.py

import cairo, math
from gi.repository import Gtk, Gdk

from .abstract_classic_tool import AbstractClassicTool
from .utilities_tools import utilities_smooth_path

class ToolShape(AbstractClassicTool):
	__gtype_name__ = 'ToolShape'

	def __init__(self, window, **kwargs):
		super().__init__('shape', _("Shape"), 'tool-freeshape-symbolic', window)
		self.use_size = True
		self._path = None

		self.reset_temp_points()
		self._style_id = 'empty'
		self._style_label = _("Empty")
		self._join_id = cairo.LineJoin.ROUND
		self._shape_id = 'polygon'
		self._shape_label = _("Polygon")

		self.add_tool_action_enum('shape_type', self._shape_id)
		self.add_tool_action_enum('shape_filling', self._style_id)
		self.add_tool_action_simple('shape_close', self.force_close_polygon)
		self.set_action_sensitivity('shape_close', False)

	def reset_temp_points(self):
		self.x_press = -1.0
		self.y_press = -1.0
		self.initial_x = -1.0
		self.initial_y = -1.0

	def set_filling_style(self):
		state_as_string = self.get_option_value('shape_filling')
		self._style_id = state_as_string
		if state_as_string == 'empty':
			self._style_label = _("Empty outline")
		elif state_as_string == 'filled':
			self._style_label = _("Main color")
		elif state_as_string == 'h-gradient':
			self._style_label = _("Horizontal gradient")
		elif state_as_string == 'v-gradient':
			self._style_label = _("Vertical gradient")
		elif state_as_string == 'r-gradient':
			self._style_label = _("Radial gradient")
		else:
			self._style_label = _("Secondary color")

	def set_active_shape(self, *args):
		self._shape_id = self.get_option_value('shape_type')
		if self._shape_id == 'rectangle':
			self._shape_label = _("Rectangle")
			self._join_id = cairo.LineJoin.MITER
		elif self._shape_id == 'oval':
			self._shape_label = _("Oval")
			self._join_id = cairo.LineJoin.ROUND
		elif self._shape_id == 'circle':
			self._shape_label = _("Circle")
			self._join_id = cairo.LineJoin.ROUND
		elif self._shape_id == 'polygon':
			self._shape_label = _("Polygon")
			self._join_id = cairo.LineJoin.MITER # BEVEL ?
		else:
			self._shape_label = _("Free shape")
			self._join_id = cairo.LineJoin.ROUND

	def get_options_label(self):
		return _("Shape options")

	def get_edition_status(self):
		self.set_filling_style()
		self.set_active_shape()
		label = self._shape_label + ' - ' + self._style_label
		if self._shape_id == 'polygon' or self._shape_id == 'freeshape':
			instruction = _("Click on the shape's first point to close it.")
			label = label + ' - ' + instruction
		else:
			self.set_action_sensitivity('shape_close', False)
		return label

	def give_back_control(self, preserve_selection):
		self.restore_pixbuf()
		self.reset_temp_points()

	############################################################################

	def on_press_on_area(self, event, surface, event_x, event_y):
		self.x_press = event_x
		self.y_press = event_y
		self.set_common_values(event.button)

	def on_motion_on_area(self, event, surface, event_x, event_y):
		if self._shape_id == 'freeshape':
			operation = self.add_point(event_x, event_y, True)
		elif self._shape_id == 'polygon':
			operation = self.add_point(event_x, event_y, False)
		else:
			if self._shape_id == 'rectangle':
				self.build_rectangle(event_x, event_y)
			elif self._shape_id == 'oval':
				self.draw_oval(event_x, event_y)
			elif self._shape_id == 'circle':
				self.draw_circle(event_x, event_y)
			operation = self.build_operation(self._path)
		self.do_tool_operation(operation)

	def on_release_on_area(self, event, surface, event_x, event_y):
		if self._shape_id == 'freeshape' or self._shape_id == 'polygon':
			operation = self.add_point(event_x, event_y, True)
			self.set_action_sensitivity('shape_close', not operation['closed'])
			if operation['closed']:
				self.apply_operation(operation)
				self.reset_temp_points()
			else:
				self.do_tool_operation(operation)
				self.non_destructive_show_modif()
		else:
			if self._shape_id == 'rectangle':
				self.build_rectangle(event_x, event_y)
			elif self._shape_id == 'oval':
				self.draw_oval(event_x, event_y)
			elif self._shape_id == 'circle':
				self.draw_circle(event_x, event_y)
			operation = self.build_operation(self._path)
			self.apply_operation(operation)
			self.reset_temp_points()

	############################################################################

	def force_close_polygon(self, *args):
		self.on_release_on_area(None, None, self.initial_x, self.initial_y)

	def add_point(self, event_x, event_y, memorize):
		"""Add a point to a shape (used by both freeshape and polygon)."""
		cairo_context = cairo.Context(self.get_surface())
		if self.initial_x == -1.0:
			# print('init polygon')
			(self.initial_x, self.initial_y) = (self.x_press, self.y_press)
			cairo_context.move_to(self.x_press, self.y_press)
			self._path = cairo_context.copy_path()
		else:
			cairo_context.append_path(self._path)
		should_close = self.should_close_shape(event_x, event_y)
		if not should_close:
			# print('continue polygon')
			cairo_context.line_to(event_x, event_y)
			cairo_context.stroke_preserve()
		if memorize:
			# print('memorize polygon')
			self._path = cairo_context.copy_path()
		operation = self.build_operation(cairo_context.copy_path())
		operation['closed'] = should_close
		return operation

	def should_close_shape(self, event_x, event_y):
		if self.initial_x == -1.0 or self.initial_y == -1.0:
			return False
		delta_x = max(event_x, self.initial_x) - min(event_x, self.initial_x)
		delta_y = max(event_y, self.initial_y) - min(event_y, self.initial_y)
		return (delta_x < self.tool_width and delta_y < self.tool_width)

	############################################################################

	def build_rectangle(self, event_x, event_y):
		cairo_context = cairo.Context(self.get_surface())
		cairo_context.move_to(self.x_press, self.y_press)
		cairo_context.line_to(self.x_press, event_y)
		cairo_context.line_to(event_x, event_y)
		cairo_context.line_to(event_x, self.y_press)
		self._path = cairo_context.copy_path()

	def draw_oval(self, event_x, event_y):
		cairo_context = cairo.Context(self.get_surface())
		x2 = (self.x_press + event_x)/2
		y2 = (self.y_press + event_y)/2
		cairo_context.curve_to(self.x_press, y2, self.x_press, event_y, x2, event_y)
		cairo_context.curve_to(x2, event_y, event_x, event_y, event_x, y2)
		cairo_context.curve_to(event_x, y2, event_x, self.y_press, x2, self.y_press)
		cairo_context.curve_to(x2, self.y_press, self.x_press, self.y_press, \
		                                                       self.x_press, y2)
		self._path = cairo_context.copy_path()

	def draw_circle(self, event_x, event_y):
		cairo_context = cairo.Context(self.get_surface())
		delta_x2 = (self.x_press - event_x) * (self.x_press - event_x)
		delta_y2 = (self.y_press - event_y) * (self.y_press - event_y)
		rayon = math.sqrt(delta_x2 + delta_y2)
		cairo_context.arc(self.x_press, self.y_press, rayon, 0.0, 2*math.pi)
		self._path = cairo_context.copy_path()

	############################################################################

	def build_operation(self, cairo_path):
		operation = {
			'tool_id': self.id,
			'rgba_main': self.main_color,
			'rgba_secd': self.secondary_color,
			'operator': cairo.Operator.OVER,
			'line_join': self._join_id,
			'line_width': self.tool_width,
			'filling': self._style_id,
			'smooth': (self._shape_id == 'freeshape'),
			'closed': True,
			'path': cairo_path
		}
		return operation

	def get_pattern_h(self, xmin, xmax):
		pattern = cairo.LinearGradient(xmin, 0.0, xmax, 0.0)
		return pattern

	def get_pattern_v(self, ymin, ymax):
		pattern = cairo.LinearGradient(0.0, ymin, 0.0, ymax)
		return pattern

	def get_pattern_r(self, center_x, center_y, rad):
		pattern = cairo.RadialGradient(center_x, center_y, 0.1 * rad, \
		                               center_x, center_y, 0.9 * rad)
		# the 2 centers could be 2 distinct points
		return pattern

	def fill_pattern(self, cairo_context, pattern, c1, c2):
		pattern.add_color_stop_rgba(0.1, c1.red, c1.green, c1.blue, c1.alpha)
		pattern.add_color_stop_rgba(0.9, c2.red, c2.green, c2.blue, c2.alpha)
		cairo_context.set_source(pattern)
		cairo_context.fill()

	def fill_secondary(self, cairo_context, c1, c2):
		cairo_context.set_source_rgba(c2.red, c2.green, c2.blue, c2.alpha)
		cairo_context.fill_preserve()
		cairo_context.set_source_rgba(c1.red, c1.green, c1.blue, c1.alpha)
		cairo_context.stroke()

	def do_tool_operation(self, operation):
		super().do_tool_operation(operation)
		cairo_context = cairo.Context(self.get_surface())
		cairo_context.set_operator(operation['operator'])
		cairo_context.set_line_width(operation['line_width'])
		cairo_context.set_line_join(operation['line_join'])
		c1 = operation['rgba_main']
		c2 = operation['rgba_secd']
		if operation['smooth']:
			utilities_smooth_path(cairo_context, operation['path'])
		else:
			cairo_context.append_path(operation['path'])
		if operation['closed']:
			cairo_context.close_path()
		filling = operation['filling']
		if filling == 'secondary':
			self.fill_secondary(cairo_context, c1, c2)
		elif filling == 'h-gradient':
			x1, y1, x2, y2 = cairo_context.path_extents()
			pattern = self.get_pattern_h(x1, x2)
			self.fill_pattern(cairo_context, pattern, c1, c2)
		elif filling == 'v-gradient':
			x1, y1, x2, y2 = cairo_context.path_extents()
			pattern = self.get_pattern_v(y1, y2)
			self.fill_pattern(cairo_context, pattern, c1, c2)
		elif filling == 'r-gradient':
			x1, y1, x2, y2 = cairo_context.path_extents()
			ddx = abs(x1 - x2) / 2
			ddy = abs(y1 - y2) / 2
			center_x = min(x1, x2) + ddx
			center_y = min(y1, y2) + ddy
			rad = max(ddx, ddy)
			pattern = self.get_pattern_r(center_x, center_y, rad)
			self.fill_pattern(cairo_context, pattern, c1, c2)
		elif filling == 'filled':
			cairo_context.set_source_rgba(c1.red, c1.green, c1.blue, c1.alpha)
			cairo_context.fill()
		else: # filling == 'empty':
			cairo_context.set_source_rgba(c1.red, c1.green, c1.blue, c1.alpha)
			cairo_context.stroke()

	############################################################################
################################################################################
