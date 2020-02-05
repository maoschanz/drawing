# tool_rectangle.py

import cairo, math
from gi.repository import Gtk, Gdk

from .abstract_tool import AbstractAbstractTool
from .utilities import utilities_generic_shape_tool_operation

class ToolRectangle(AbstractAbstractTool):
	__gtype_name__ = 'ToolRectangle'

	def __init__(self, window, **kwargs):
		super().__init__('rectangle', _("Rectangle"), 'tool-rectangle-symbolic', window)
		self.use_size = True

		(self.x_press, self.y_press) = (-1.0, -1.0)
		self.selected_style_label = _("Filled (secondary color)")
		self.selected_style_id = 'secondary'
		self.selected_shape_id = 'rectangle'

		self.add_tool_action_enum('filling_style', self.selected_style_id)
		self.add_tool_action_enum('rectangle_shape', self.selected_shape_id)

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
		self.selected_shape_id = self.get_option_value('rectangle_shape')

	def get_options_label(self):
		return _("Rectangle options")

	def get_edition_status(self):
		self.set_active_shape()
		self.set_active_style()
		if self.selected_shape_id == 'rounded':
			label = _("Rounded rectangle") + ' - ' + self.selected_style_label
		else:
			label = self.label + ' - ' + self.selected_style_label
		return label

	def give_back_control(self, preserve_selection):
		(self.x_press, self.y_press) = (-1.0, -1.0)
		self.restore_pixbuf()

	############################################################################

	def build_rectangle(self, event_x, event_y):
		cairo_context = cairo.Context(self.get_surface())
		cairo_context.move_to(self.x_press, self.y_press)
		cairo_context.line_to(self.x_press, event_y)
		cairo_context.line_to(event_x, event_y)
		cairo_context.line_to(event_x, self.y_press)
		cairo_context.close_path()
		self._path = cairo_context.copy_path()

	def build_roundedrect(self, event_x, event_y):
		cairo_context = cairo.Context(self.get_surface())
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

	############################################################################

	def on_press_on_area(self, event, surface, tool_width, left_color, right_color, event_x, event_y):
		self.x_press = event_x
		self.y_press = event_y
		self.tool_width = tool_width
		if event.button == 3:
			self.main_color = right_color
			self.secondary_color = left_color
		else:
			self.main_color = left_color
			self.secondary_color = right_color

	def on_motion_on_area(self, event, surface, event_x, event_y):
		if self.selected_shape_id == 'rectangle':
			self.build_rectangle(event_x, event_y)
		else:
			self.build_roundedrect(event_x, event_y)
		operation = self.build_operation()
		self.do_tool_operation(operation)

	def on_release_on_area(self, event, surface, event_x, event_y):
		if self.selected_shape_id == 'rectangle':
			self.build_rectangle(event_x, event_y)
		else:
			self.build_roundedrect(event_x, event_y)
		self.x_press = 0.0
		self.y_press = 0.0
		operation = self.build_operation()
		self.apply_operation(operation)

	############################################################################

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'rgba_main': self.main_color,
			'rgba_secd': self.secondary_color,
			'operator': cairo.Operator.OVER,
			'line_join': cairo.LineJoin.MITER,
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

	############################################################################
################################################################################

