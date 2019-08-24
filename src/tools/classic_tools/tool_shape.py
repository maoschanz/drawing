# tool_shape.py

from gi.repository import Gtk, Gdk
import cairo, math

from .abstract_classic_tool import AbstractClassicTool
from .utilities import utilities_smooth_path

class ToolShape(AbstractClassicTool):
	__gtype_name__ = 'ToolShape'

	def __init__(self, window, **kwargs):
		super().__init__('shape', _("Shape"), 'tool-freeshape-symbolic', window)
		self.use_size = True
		self._path = None

		self.reset_temp_points()
		self.selected_style_id = 'empty'
		self.selected_style_label = _("Empty")
		self.selected_join_id = cairo.LineJoin.ROUND
		self.selected_shape_id = 'polygon'
		self.selected_shape_label = _("Polygon")

		self.add_tool_action_enum('shape_type', self.selected_shape_id)
		self.add_tool_action_enum('shape_filling', self.selected_style_id)

	def reset_temp_points(self):
		self.x_press = -1.0
		self.y_press = -1.0
		self.past_x = -1.0
		self.past_y = -1.0

	def set_filling_style(self):
		state_as_string = self.get_option_value('shape_filling')
		self.selected_style_id = state_as_string
		if state_as_string == 'empty':
			self.selected_style_label = _("Empty")
		elif state_as_string == 'filled':
			self.selected_style_label = _("Filled (main color)")
		else:
			self.selected_style_label = _("Filled (secondary color)")

	def set_active_shape(self, *args):
		self.selected_shape_id = self.get_option_value('shape_type')
		if self.selected_shape_id == 'rectangle':
			self.selected_shape_label = _("Rectangle")
			self.selected_join_id = cairo.LineJoin.MITER
		elif self.selected_shape_id == 'oval':
			self.selected_shape_label = _("Oval")
			self.selected_join_id = cairo.LineJoin.ROUND
		elif self.selected_shape_id == 'circle':
			self.selected_shape_label = _("Circle")
			self.selected_join_id = cairo.LineJoin.ROUND
		elif self.selected_shape_id == 'polygon':
			self.selected_shape_label = _("Polygon")
			self.selected_join_id = cairo.LineJoin.MITER # BEVEL ?
		else:
			self.selected_shape_label = _("Free shape")
			self.selected_join_id = cairo.LineJoin.ROUND

	def get_options_label(self):
		return _("Shape options")

	def get_edition_status(self):
		self.set_filling_style()
		self.set_active_shape()
		label = self.selected_shape_label + ' - ' + self.selected_style_label
		if self.selected_shape_id == 'polygon' or self.selected_shape_id == 'freeshape':
			instruction = _("Click on the shape's first point to close it.")
			label = label + ' - ' + instruction
		return label

	def give_back_control(self, preserve_selection):
		self.restore_pixbuf()
		self.reset_temp_points()

	############################################################################

	def on_press_on_area(self, area, event, surface, event_x, event_y):
		self.x_press = event_x
		self.y_press = event_y
		self.set_common_values(event)

	def on_motion_on_area(self, area, event, surface, event_x, event_y):
		if self.selected_shape_id == 'freeshape':
			operation = self.add_point(event_x, event_y, True)
		elif self.selected_shape_id == 'polygon':
			operation = self.add_point(event_x, event_y, False)
		else:
			if self.selected_shape_id == 'rectangle':
				self.build_rectangle(event_x, event_y)
			elif self.selected_shape_id == 'oval':
				self.draw_oval(event_x, event_y)
			elif self.selected_shape_id == 'circle':
				self.draw_circle(event_x, event_y)
			operation = self.build_operation(self._path)
		self.do_tool_operation(operation)

	def on_release_on_area(self, area, event, surface, event_x, event_y):
		if self.selected_shape_id == 'freeshape' or self.selected_shape_id == 'polygon':
			operation = self.add_point(event_x, event_y, True)
			if operation['closed']:
				self.apply_operation(operation)
				self.reset_temp_points()
			else:
				self.do_tool_operation(operation)
				self.non_destructive_show_modif()
		else:
			if self.selected_shape_id == 'rectangle':
				self.build_rectangle(event_x, event_y)
			elif self.selected_shape_id == 'oval':
				self.draw_oval(event_x, event_y)
			elif self.selected_shape_id == 'circle':
				self.draw_circle(event_x, event_y)
			operation = self.build_operation(self._path)
			self.apply_operation(operation)
			self.reset_temp_points()

	############################################################################

	def add_point(self, event_x, event_y, memorize):
		"""Add a point to a shape (used by both freeshape and polygon)."""
		cairo_context = cairo.Context(self.get_surface())
		if self.past_x == -1.0:
			# print('init polygon')
			(self.past_x, self.past_y) = (self.x_press, self.y_press)
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
		if self.past_x == -1.0 or self.past_y == -1.0:
			return False
		delta_x = max(event_x, self.past_x) - min(event_x, self.past_x)
		delta_y = max(event_y, self.past_y) - min(event_y, self.past_y)
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
		rayon = math.sqrt((self.x_press - event_x)*(self.x_press - event_x) \
		                    + (self.y_press - event_y)*(self.y_press - event_y))
		cairo_context.arc(self.x_press, self.y_press, rayon, 0.0, 2*math.pi)
		self._path = cairo_context.copy_path()

	############################################################################

	def build_operation(self, cairo_path):
		operation = {
			'tool_id': self.id,
			'rgba_main': self.main_color,
			'rgba_secd': self.secondary_color,
			'operator': cairo.Operator.OVER,
			'line_join': self.selected_join_id,
			'line_width': self.tool_width,
			'filling': self.selected_style_id,
			'smooth': (self.selected_shape_id == 'freeshape'),
			'closed': True,
			'path': cairo_path
		}
		return operation

	def do_tool_operation(self, operation):
		if operation['tool_id'] != self.id:
			return
		self.restore_pixbuf()
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
			cairo_context.set_source_rgba(c2.red, c2.green, c2.blue, c2.alpha)
			cairo_context.fill_preserve()
		cairo_context.set_source_rgba(c1.red, c1.green, c1.blue, c1.alpha)
		if filling == 'filled':
			cairo_context.fill()
		else:
			cairo_context.stroke()

	############################################################################
################################################################################
