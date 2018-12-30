# shape.py

from gi.repository import Gtk, Gdk, Gio, GLib
import cairo
import math

from .tools import ToolTemplate

class ToolPolygon(ToolTemplate):
	__gtype_name__ = 'ToolPolygon'

	use_size = True

	def __init__(self, window, **kwargs):
		super().__init__('polygon', _("Polygon"), 'non-starred-symbolic', window)

		(self.x_press, self.y_press) = (-1.0, -1.0)
		(self.past_x, self.past_y) = (-1.0, -1.0)
		self.selected_style_id = 'secondary'
		self.selected_style_label = _("Filled (secondary color)")
		self.use_freehand = False

		# Building the widget containing options
		builder = Gtk.Builder.new_from_resource("/com/github/maoschanz/Drawing/tools/ui/polygon.ui")
		model = builder.get_object('options-menu')
		self.options_menu = Gtk.Popover.new_from_model(window.options_btn, model)
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

	def get_options_widget(self):
		return self.options_menu

	def get_options_label(self):
		if self.use_freehand:
			return _("Freehand") + ' - ' + self.selected_style_label
		else:
			return _("Edges") + ' - ' + self.selected_style_label

	def give_back_control(self):
		self.restore_pixbuf()
		if (self.x_press, self.y_press) == (-1.0, -1.0):
			return False
		else:
			(self.x_press, self.y_press) = (-1.0, -1.0)
			(self.past_x, self.past_y) = (-1.0, -1.0)
			return True

	def draw_polygon(self, event, is_preview):
		w_context = cairo.Context(self.window.get_surface())
		w_context.set_line_width(self.tool_width)

		if self.past_x == -1.0:
			self.init_polygon(w_context)
		else:
			w_context.append_path(self._path)

		if is_preview:
			self.preview_polygon(w_context, event.x, event.y)
			return False

		if self.past_x != -1.0 and self.past_y != -1.0 \
		and (max(event.x, self.past_x) - min(event.x, self.past_x) < self.tool_width) \
		and (max(event.y, self.past_y) - min(event.y, self.past_y) < self.tool_width):
			self.finish_polygon(w_context)
			return True
		else:
			self.continue_polygon(w_context, event.x, event.y)
			return False

	def init_polygon(self, w_context):
		(self.past_x, self.past_y) = (self.x_press, self.y_press)
		w_context.move_to(self.x_press, self.y_press)
		self._path = w_context.copy_path()

	def continue_polygon(self, w_context, x, y):
		w_context.line_to(x, y)
		w_context.stroke_preserve() # draw the line without closing the path
		self._path = w_context.copy_path()
		self.non_destructive_show_modif()

	def finish_polygon(self, w_context):
		w_context.close_path()
		w_context.set_source_rgba(self.main_color.red, self.main_color.green, \
			self.main_color.blue, self.main_color.alpha)
		if self.selected_style_id == 'filled':
			w_context.fill()
		elif self.selected_style_id == 'secondary':
			w_context.set_source_rgba(self.secondary_color.red, self.secondary_color.green, \
				self.secondary_color.blue, self.secondary_color.alpha)
			w_context.fill_preserve() # TODO c'est élégant ça, je devrais le faire ailleurs
			w_context.set_source_rgba(self.main_color.red, self.main_color.green, \
				self.main_color.blue, self.main_color.alpha)
			w_context.stroke()
		else:
			w_context.stroke()

	def preview_polygon(self, w_context, x, y):
		w_context.line_to(x, y)
		self.finish_polygon(w_context)

	def on_motion_on_area(self, area, event, surface):
		self.restore_pixbuf()
		if self.use_freehand:
			self.draw_polygon(event, False)
		else:
			self.draw_polygon(event, True)

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color):
		self.x_press = event.x
		self.y_press = event.y
		self.tool_width = tool_width
		if event.button == 3:
			self.main_color = right_color
			self.secondary_color = left_color
		else:
			self.main_color = left_color
			self.secondary_color = right_color

	def on_release_on_area(self, area, event, surface):
		self.restore_pixbuf()
		finished = self.draw_polygon(event, False)
		if finished:
			self.apply_to_pixbuf()
			(self.x_press, self.y_press) = (-1.0, -1.0)
			(self.past_x, self.past_y) = (-1.0, -1.0)

