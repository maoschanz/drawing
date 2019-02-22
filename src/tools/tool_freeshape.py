# tool_freeshape.py

from gi.repository import Gtk, Gdk
import cairo

from .tools import ToolTemplate

class ToolFreeshape(ToolTemplate):
	__gtype_name__ = 'ToolFreeshape'

	implements_panel = False

	def __init__(self, window, **kwargs):
		super().__init__('freeshape', _("Free shape"), 'tool-polygon-symbolic', window, False)
		self.use_size = True

		(self.x_press, self.y_press) = (-1.0, -1.0)
		(self.past_x, self.past_y) = (-1.0, -1.0)
		self.selected_style_id = 'secondary'
		self.selected_style_label = _("Filled (secondary color)")

		self.add_tool_action_enum('filling_style', 'secondary')

	def set_filling_style(self):
		state_as_string = self.get_option_value('filling_style')
		self.selected_style_id = state_as_string
		if state_as_string == 'empty':
			self.selected_style_label = _("Empty")
		elif state_as_string == 'filled':
			self.selected_style_label = _("Filled (main color)")
		else:
			self.selected_style_label = _("Filled (secondary color)")

	def get_options_model(self):
		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/Drawing/tools/ui/tool_freeshape.ui')
		return builder.get_object('options-menu')

	def get_options_label(self):
		return _("Shape options")

	def get_edition_status(self):
		label = self.label + ' - ' + self.selected_style_label
		return label

	def give_back_control(self):
		self.restore_pixbuf()
		if (self.x_press, self.y_press) == (-1.0, -1.0):
			return False
		else:
			(self.x_press, self.y_press) = (-1.0, -1.0)
			(self.past_x, self.past_y) = (-1.0, -1.0)
			return True

	def draw_polygon(self, event_x, event_y):
		w_context = cairo.Context(self.get_surface())
		w_context.set_line_width(self.tool_width)
		w_context.set_line_join(cairo.LineJoin.ROUND)

		if self.past_x == -1.0:
			self.init_polygon(w_context)
		else:
			w_context.append_path(self._path)

		if self.past_x != -1.0 and self.past_y != -1.0 \
		and (max(event_x, self.past_x) - min(event_x, self.past_x) < self.tool_width) \
		and (max(event_y, self.past_y) - min(event_y, self.past_y) < self.tool_width):
			w_context.close_path()
			self._path = w_context.copy_path()
			return True
		else:
			self.continue_polygon(w_context, event_x, event_y)
			return False

	def init_polygon(self, w_context): # TODO simplfiable depuis que c'est split en 2 outils
		(self.past_x, self.past_y) = (self.x_press, self.y_press)
		w_context.move_to(self.x_press, self.y_press)
		self._path = w_context.copy_path()

	def continue_polygon(self, w_context, x, y):
		w_context.set_line_width(self.tool_width)
		w_context.set_source_rgba(self.main_color.red, self.main_color.green, \
			self.main_color.blue, self.main_color.alpha)
		w_context.line_to(x, y)
		w_context.stroke_preserve() # draw the line without closing the path
		self._path = w_context.copy_path()
		self.non_destructive_show_modif()

	def finish_polygon(self, w_context):
		w_context.close_path()
		operation = self.build_operation(w_context.copy_path())
		self.do_tool_operation(operation)
		return

	def on_motion_on_area(self, area, event, surface, event_x, event_y):
		self.restore_pixbuf()
		self.draw_polygon(event_x, event_y)

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
		self.set_filling_style()

	def on_release_on_area(self, area, event, surface, event_x, event_y):
		self.restore_pixbuf()
		finished = self.draw_polygon(event_x, event_y)
		if finished:
			operation = self.build_operation(self._path)
			self.apply_operation(operation)
			(self.x_press, self.y_press) = (-1.0, -1.0)
			(self.past_x, self.past_y) = (-1.0, -1.0)

	def build_operation(self, cairo_path):
		operation = {
			'tool_id': self.id,
			'rgba_main': self.main_color,
			'rgba_secd': self.secondary_color,
			'operator': cairo.Operator.OVER,
			'line_join': cairo.LineJoin.ROUND,
			'line_width': self.tool_width,
			'filling': self.selected_style_id,
			'path': cairo_path
		}
		return operation

	def do_tool_operation(self, operation):
		if operation['tool_id'] != self.id:
			return
		self.restore_pixbuf()
		w_context = cairo.Context(self.get_surface())
		w_context.set_operator(operation['operator'])
		w_context.set_line_width(operation['line_width'])
		w_context.set_line_join(operation['line_join'])
		rgba_main = operation['rgba_main']
		rgba_secd = operation['rgba_secd']
		w_context.append_path(operation['path'])
		filling = operation['filling']
		if filling == 'secondary':
			w_context.set_source_rgba(rgba_secd.red, rgba_secd.green, rgba_secd.blue, rgba_secd.alpha)
			w_context.fill_preserve()
			w_context.set_source_rgba(rgba_main.red, rgba_main.green, rgba_main.blue, rgba_main.alpha)
			w_context.stroke()
		elif filling == 'filled':
			w_context.set_source_rgba(rgba_main.red, rgba_main.green, rgba_main.blue, rgba_main.alpha)
			w_context.fill()
		else:
			w_context.set_source_rgba(rgba_main.red, rgba_main.green, rgba_main.blue, rgba_main.alpha)
			w_context.stroke()
