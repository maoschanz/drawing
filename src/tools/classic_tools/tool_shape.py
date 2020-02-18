# tool_shape.py
#
# Copyright 2018-2020 Romain F. T.
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
from .abstract_classic_tool import AbstractClassicTool
from .utilities_paths import utilities_smooth_path

class ToolShape(AbstractClassicTool):
	__gtype_name__ = 'ToolShape'

	def __init__(self, window, **kwargs):
		super().__init__('shape', _("Shape"), 'tool-freeshape-symbolic', window)
		self.reset_temp_points()

		self._shape_id = self.get_settings().get_string('last-active-shape')
		self.add_tool_action_enum('shape_type', self._shape_id)
		self.set_active_shape()

		self._style_id = 'empty'
		self._style_label = _("Empty")
		self.add_tool_action_enum('shape_filling', self._style_id)

		self.add_tool_action_simple('shape_close', self.force_close_polygon)
		self.set_action_sensitivity('shape_close', False)

	def reset_temp_points(self):
		self._path = None
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
		else: # if state_as_string == 'secondary':
			self._style_label = _("Secondary color")

	def set_active_shape(self, *args):
		self._shape_id = self.get_option_value('shape_type')
		if self._shape_id == 'rectangle':
			self._shape_label = _("Rectangle")
			self._join_id = cairo.LineJoin.MITER
		elif self._shape_id == 'roundedrect':
			self._shape_label = _("Rounded rectangle")
			self._join_id = cairo.LineJoin.ROUND
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
		self.last_mouse_btn = event.button
		self.set_common_values(self.last_mouse_btn, event_x, event_y)

	def on_motion_on_area(self, event, surface, event_x, event_y):
		if self._shape_id == 'freeshape':
			operation = self.add_point(event_x, event_y, True)
		elif self._shape_id == 'polygon':
			operation = self.add_point(event_x, event_y, False)
		else:
			if self._shape_id == 'rectangle':
				self.build_rectangle(event_x, event_y)
			elif self._shape_id == 'roundedrect':
				self.build_roundedrect(event_x, event_y)
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
			elif self._shape_id == 'roundedrect':
				self.build_roundedrect(event_x, event_y)
			elif self._shape_id == 'oval':
				self.draw_oval(event_x, event_y)
			elif self._shape_id == 'circle':
				self.draw_circle(event_x, event_y)
			operation = self.build_operation(self._path)
			self.apply_operation(operation)
			self.reset_temp_points()

	############################################################################

	def force_close_polygon(self, *args):
		self.set_common_values(self.last_mouse_btn, self.x_press, self.y_press)
		self.on_release_on_area(None, None, self.initial_x, self.initial_y)

	def add_point(self, event_x, event_y, memorize):
		"""Add a point to a shape (used by both freeshape and polygon)."""
		cairo_context = self.get_context()
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
		cairo_context = self.get_context()
		cairo_context.move_to(self.x_press, self.y_press)
		cairo_context.line_to(self.x_press, event_y)
		cairo_context.line_to(event_x, event_y)
		cairo_context.line_to(event_x, self.y_press)
		cairo_context.close_path()
		self._path = cairo_context.copy_path()

	def build_roundedrect(self, event_x, event_y):
		cairo_context = self.get_context()
		a = min(self.x_press, event_x)
		b = max(self.x_press, event_x)
		c = min(self.y_press, event_y)
		d = max(self.y_press, event_y)
		radius = min(d - c, b - a) / 6 # c'est arbitraire
		pi2 = math.pi / 2
		cairo_context.arc(a + radius, c + radius, radius, 2 * pi2, 3 * pi2)
		cairo_context.arc(b - radius, c + radius, radius, 3 * pi2, 4 * pi2)
		cairo_context.arc(b - radius, d - radius, radius, 0 * pi2, 1 * pi2)
		cairo_context.arc(a + radius, d - radius, radius, 1 * pi2, 2 * pi2)
		cairo_context.close_path()
		self._path = cairo_context.copy_path()

	def draw_oval(self, event_x, event_y):
		cairo_context = self.get_context()
		saved_matrix = cairo_context.get_matrix()
		halfw = (self.x_press - event_x) / 2
		halfh = (self.y_press - event_y) / 2
		cairo_context.translate(event_x + halfw, event_y + halfh)
		cairo_context.scale(halfw, halfh)
		cairo_context.arc(0, 0, 1, 0, 2 * math.pi)
		cairo_context.set_matrix(saved_matrix)
		cairo_context.close_path()
		self._path = cairo_context.copy_path()

	def draw_circle(self, event_x, event_y):
		cairo_context = self.get_context()
		delta_x2 = (self.x_press - event_x) * (self.x_press - event_x)
		delta_y2 = (self.y_press - event_y) * (self.y_press - event_y)
		rayon = math.sqrt(delta_x2 + delta_y2)
		cairo_context.arc(self.x_press, self.y_press, rayon, 0.0, 2 * math.pi)
		self._path = cairo_context.copy_path()

	############################################################################

	def build_operation(self, cairo_path):
		operation = {
			'tool_id': self.id,
			'rgba_main': self.main_color,
			'rgba_secd': self.secondary_color,
			'antialias': self._use_antialias,
			'operator': cairo.Operator.OVER, # self._operator, # XXX ne marche pas avec le blur
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
		"""Fill the shape defined by the context with a gradient from c1 to c2
		according to the given pattern."""
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
		cairo_context = self.start_tool_operation(operation)
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
