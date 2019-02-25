# tool_rectangle.py

from gi.repository import Gtk, Gdk
import cairo

from .tools import ToolTemplate
from .utilities import utilities_generic_shape_tool_operation

class ToolRectangle(ToolTemplate):
	__gtype_name__ = 'ToolRectangle'

	implements_panel = False

	def __init__(self, window, **kwargs):
		super().__init__('rectangle', _("Rectangle"), 'tool-rectangle-symbolic', window, False)
		self.use_size = True

		(self.x_press, self.y_press) = (-1.0, -1.0)
		self.selected_style_label = _("Filled (secondary color)")
		self.selected_style_id = 'secondary'

		self.add_tool_action_enum('filling_style', 'secondary')

	def set_filling_style(self, *args):
		state_as_string = self.get_option_value('filling_style')
		self.selected_style_id = state_as_string
		if state_as_string == 'empty':
			self.selected_style_label = _("Empty")
		elif state_as_string == 'filled':
			self.selected_style_label = _("Filled (main color)")
		else:
			self.selected_style_label = _("Filled (secondary color)")

	def get_options_model(self):
		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/Drawing/tools/ui/tool_rectangle.ui')
		return builder.get_object('options-menu')

	def get_options_label(self):
		return _("Rectangle options")

	def get_edition_status(self):
		self.set_filling_style()
		label = self.label + ' - ' + self.selected_style_label
		return label

	def give_back_control(self):
		(self.x_press, self.y_press) = (-1.0, -1.0)
		self.restore_pixbuf()
		return False

	def build_rectangle(self, event_x, event_y):
		cairo_context = cairo.Context(self.get_surface())
		cairo_context.move_to(self.x_press, self.y_press)
		cairo_context.line_to(self.x_press, event_y)
		cairo_context.line_to(event_x, event_y)
		cairo_context.line_to(event_x, self.y_press)
		cairo_context.close_path()
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
		self.build_rectangle(event_x, event_y)
		operation = self.build_operation()
		self.do_tool_operation(operation)

	def on_release_on_area(self, area, event, surface, event_x, event_y):
		self.build_rectangle(event_x, event_y)
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

