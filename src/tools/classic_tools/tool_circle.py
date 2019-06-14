# tool_circle.py

from gi.repository import Gtk, Gdk
import cairo, math

from .abstract_tool import ToolTemplate
from .utilities import utilities_generic_shape_tool_operation

class ToolCircle(ToolTemplate):
	__gtype_name__ = 'ToolCircle'

	def __init__(self, window, **kwargs):
		super().__init__('circle', _("Circle"), 'tool-circle-symbolic', window)
		self.use_size = True

		(self.x_press, self.y_press) = (-1.0, -1.0)
		self.selected_style_label = _("Filled (secondary color)")
		self.selected_shape_label = _("Circle")
		self.selected_style_id = 'secondary'
		self.selected_shape_id = 'circle'

		self.add_tool_action_enum('circle_shape', 'circle')

	def set_active_style(self, *args):
		state_as_string = self.get_option_value('filling_style')
		self.selected_style_id = state_as_string
		if state_as_string == 'empty':
			self.selected_style_label = _("Empty")
		elif state_as_string == 'filled':
			self.selected_style_label = _("Filled (main color)")
		else:
			self.selected_style_label = _("Filled (secondary color)")

	def set_active_shape(self, *args):
		self.selected_shape_id = self.get_option_value('circle_shape')

	def get_options_label(self):
		return _("Circle options")

	def get_edition_status(self):
		self.set_active_shape()
		self.set_active_style()
		if self.selected_shape_id == 'oval':
			label = _("Oval") + ' - ' + self.selected_style_label
		else:
			label = self.label + ' - ' + self.selected_style_label
		return label

	def give_back_control(self, preserve_selection):
		(self.x_press, self.y_press) = (-1.0, -1.0)
		self.restore_pixbuf()

	def draw_oval(self, event_x, event_y):
		cairo_context = cairo.Context(self.get_surface())
		cairo_context.curve_to(self.x_press, (self.y_press+event_y)/2, \
			self.x_press, event_y, (self.x_press+event_x)/2, event_y)
		cairo_context.curve_to((self.x_press+event_x)/2, event_y, \
			event_x, event_y, event_x, (self.y_press+event_y)/2)
		cairo_context.curve_to(event_x, (self.y_press+event_y)/2, \
			event_x, self.y_press, (self.x_press+event_x)/2, self.y_press)
		cairo_context.curve_to((self.x_press+event_x)/2, self.y_press, \
			self.x_press, self.y_press, self.x_press, (self.y_press+event_y)/2)
		cairo_context.close_path()
		self._path = cairo_context.copy_path()

	def draw_circle(self, event_x, event_y):
		cairo_context = cairo.Context(self.get_surface())
		rayon = math.sqrt((self.x_press - event_x)*(self.x_press - event_x) \
			+ (self.y_press - event_y)*(self.y_press - event_y))
		cairo_context.arc(self.x_press, self.y_press, rayon, 0.0, 2*math.pi)
		self._path = cairo_context.copy_path()

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color, event_x, event_y):
		self.x_press = event_x
		self.y_press = event_y
		self.tool_width = tool_width
		if event.button == 3:
			self.main_color = right_color
			self.secondary_color = left_color
		else:
			self.main_color = left_color
			self.secondary_color = right_color

	def on_motion_on_area(self, area, event, surface, event_x, event_y):
		self.restore_pixbuf()
		if self.selected_shape_id == 'oval':
			self.draw_oval(event_x, event_y)
		elif self.selected_shape_id == 'circle':
			self.draw_circle(event_x, event_y)
		operation = self.build_operation()
		self.do_tool_operation(operation)

	def on_release_on_area(self, area, event, surface, event_x, event_y):
		if self.selected_shape_id == 'oval':
			self.draw_oval(event_x, event_y)
		elif self.selected_shape_id == 'circle':
			self.draw_circle(event_x, event_y)
		self.x_press = 0.0
		self.y_press = 0.0
		operation = self.build_operation()
		self.apply_operation(operation)

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'rgba_main': self.main_color,
			'rgba_secd': self.secondary_color,
			'operator': cairo.Operator.OVER,
			'line_join': cairo.LineJoin.ROUND,
			'line_width': self.tool_width,
			'filling': self.selected_style_id,
			'path': self._path
		}
		return operation

	def do_tool_operation(self, operation):
		if operation['tool_id'] != self.id:
			return
		self.restore_pixbuf()
		cairo_context = cairo.Context(self.get_surface())
		utilities_generic_shape_tool_operation(cairo_context, operation)

