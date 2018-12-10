# shape.py

from gi.repository import Gtk, Gdk, Gio
import cairo
import math

from .tools import ToolTemplate

class ToolPolygon(ToolTemplate):
	__gtype_name__ = 'ToolPolygon'

	use_size = True
	style_btns = {}

	def __init__(self, window, **kwargs):
		super().__init__('polygon', _("Polygon"), 'non-starred-symbolic', window)

		(self.x_press, self.y_press) = (-1.0, -1.0)
		(self.past_x, self.past_y) = (-1.0, -1.0)

		# Building the widget containing options
		builder = Gtk.Builder()
		builder.add_from_resource("/com/github/maoschanz/Drawing/tools/ui/polygon.ui")
		self.options_box = builder.get_object("options_box")

		self.freehand_switch = builder.get_object('freehand-switch')

		self.style_btns['empty'] = builder.get_object("style_btn_1")
		self.style_btns['filled'] = builder.get_object("style_btn_2")
		self.style_btns['secondary'] = builder.get_object("style_btn_3")

		for type_id in self.style_btns:
			self.style_btns[type_id].connect('toggled', self.on_style_changed, type_id)

		self.style_btns['secondary'].set_active(True)

	def on_style_changed(self, *args):
		self.selected_style_label = args[0].get_label()
		self.selected_style_id = args[1]

	def get_options_widget(self):
		return self.options_box

	def get_options_label(self):
		if self.freehand_switch.get_active():
			return _("Freehand") + ' - ' + self.selected_style_label
		else:
			return _("Edges") + ' - ' + self.selected_style_label

	def give_back_control(self):
		(self.x_press, self.y_press) = (-1.0, -1.0)
		(self.past_x, self.past_y) = (-1.0, -1.0)
		self.restore_pixbuf()

	def draw_polygon(self, event, is_preview):
		w_context = cairo.Context(self.window.get_surface())
		w_context.set_line_width(self.tool_width)

		if self.past_x == -1.0:
			self.init_polygon(w_context)
		else:
			w_context.append_path(self.path)

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
		self.path = w_context.copy_path()

	def continue_polygon(self, w_context, x, y):
		w_context.line_to(x, y)
		w_context.stroke_preserve() # draw the line without closing the path
		self.path = w_context.copy_path()
		self.non_destructive_show_modif()

	def finish_polygon(self, w_context):
		w_context.close_path()
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
		if self.freehand_switch.get_active():
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
		print(finished)
		if finished:
			self.apply_to_pixbuf()
			(self.x_press, self.y_press) = (-1.0, -1.0)
			(self.past_x, self.past_y) = (-1.0, -1.0)

