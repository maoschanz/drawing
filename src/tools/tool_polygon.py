# tool_polygon.py

from gi.repository import Gtk, Gdk, Gio, GLib
import cairo
import math

from .tools import ToolTemplate

class ToolPolygon(ToolTemplate):
	__gtype_name__ = 'ToolPolygon'

	use_size = True
	implements_panel = False

	def __init__(self, window, **kwargs):
		super().__init__('polygon', _("Polygon"), 'tool-polygon-symbolic', window, False)

		(self.x_press, self.y_press) = (-1.0, -1.0)
		(self.past_x, self.past_y) = (-1.0, -1.0)
		self.selected_style_id = 'secondary'
		self.selected_style_label = _("Filled (secondary color)")
		self.use_freehand = False

		self.add_tool_action_enum('polygon_style', 'secondary', self.on_change_active_style)
		self.add_tool_action_boolean('polygon_freehand', False, self.set_freehand)

	def set_freehand(self, *args):
		if not args[0].get_state():
			self.use_freehand = True
			args[0].set_state(GLib.Variant.new_boolean(True))
		else:
			self.use_freehand = False
			args[0].set_state(GLib.Variant.new_boolean(False))

	def on_change_active_style(self, *args):
		state_as_string = args[1].get_string()
		if state_as_string == args[0].get_state().get_string():
			return
		args[0].set_state(GLib.Variant.new_string(state_as_string))
		self.selected_style_id = state_as_string
		if state_as_string == 'empty':
			self.selected_style_label = _("Empty")
		elif state_as_string == 'filled':
			self.selected_style_label = _("Filled (main color)")
		else:
			self.selected_style_label = _("Filled (secondary color)")

	def get_options_model(self):
		builder = Gtk.Builder.new_from_resource("/com/github/maoschanz/Drawing/tools/ui/tool_polygon.ui")
		return builder.get_object('options-menu')

	def get_options_label(self):
		if self.use_freehand:
			return _("Freehand")
		else:
			return _("Edges")

	def get_edition_status(self):
		if self.use_freehand:
			label = _("Freehand") + ' - ' + self.selected_style_label
		else:
			label = _("Edges") + ' - ' + self.selected_style_label
		return label

	def give_back_control(self):
		self.restore_pixbuf()
		if (self.x_press, self.y_press) == (-1.0, -1.0):
			return False
		else:
			(self.x_press, self.y_press) = (-1.0, -1.0)
			(self.past_x, self.past_y) = (-1.0, -1.0)
			return True

	# def cancel_ongoing_operation(self):
		# TODO

	def draw_polygon(self, event_x, event_y, is_preview):
		w_context = cairo.Context(self.get_surface())
		w_context.set_line_width(self.tool_width)

		if self.past_x == -1.0:
			self.init_polygon(w_context)
		else:
			w_context.append_path(self._path)

		if is_preview:
			self.preview_polygon(w_context, event_x, event_y)
			return False

		if self.past_x != -1.0 and self.past_y != -1.0 \
		and (max(event_x, self.past_x) - min(event_x, self.past_x) < self.tool_width) \
		and (max(event_y, self.past_y) - min(event_y, self.past_y) < self.tool_width):
			w_context.close_path()
			self._path = w_context.copy_path()
			return True
		else:
			self.continue_polygon(w_context, event_x, event_y)
			return False

	def init_polygon(self, w_context):
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

	def preview_polygon(self, w_context, x, y):
		w_context.line_to(x, y)
		w_context.close_path()
		operation = self.build_operation(w_context.copy_path())
		self.do_tool_operation(operation)

	def on_motion_on_area(self, area, event, surface, event_x, event_y):
		self.restore_pixbuf()
		if self.use_freehand:
			self.draw_polygon(event_x, event_y, False)
		else:
			self.draw_polygon(event_x, event_y, True)

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

	def on_release_on_area(self, area, event, surface, event_x, event_y):
		self.restore_pixbuf()
		finished = self.draw_polygon(event_x, event_y, False)
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
			'line_width': self.tool_width,
			'filling': self.selected_style_id,
			'path': cairo_path
		}
		return operation

	def do_tool_operation(self, operation): # TODO pas le mme line_join si on trace à main levée
		if operation['tool_id'] != self.id:
			return
		self.restore_pixbuf()
		w_context = cairo.Context(self.get_surface())
		w_context.set_operator(operation['operator'])
		w_context.set_line_width(operation['line_width'])
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
