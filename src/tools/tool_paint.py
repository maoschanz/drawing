# tool_paint.py

from gi.repository import Gtk, Gdk, GdkPixbuf
import cairo

from .tools import ToolTemplate
from .utilities import utilities_get_magic_path
from .utilities import utilities_get_rgb_for_xy

class ToolPaint(ToolTemplate):
	__gtype_name__ = 'ToolPaint'

	implements_panel = False

	def __init__(self, window, **kwargs):
		super().__init__('paint', _("Paint"), 'tool-paint-symbolic', window, False)
		self.new_color = None
		self.magic_path = None
		self.use_size = False

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color, event_x, event_y):
		print("press")
		if event.button == 1:
			self.new_color = left_color
		if event.button == 3:
			self.new_color = right_color

	def on_release_on_area(self, area, event, surface, event_x, event_y):
		# Guard clause: we can't paint outside of the surface
		if event.x < 0 or event.x > surface.get_width() \
		or event.y < 0 or event.y > surface.get_height():
			return

		(x, y) = (int(event.x), int(event.y))

		self.old_color = utilities_get_rgb_for_xy(surface, x, y)
		# self.magic_path = utilities_get_magic_path(surface, x, y, self.window, 2) # Better if using the second method

		self.magic_path = utilities_get_magic_path(surface, x, y, self.window, 1)

		operation = self.build_operation()
		self.apply_operation(operation)

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'rgba': self.new_color,
			'old_rgba': self.old_color,
			'path': self.magic_path
		}
		return operation

	# def do_tool_operation(self, operation): # Moins laid mais piêtre gestion des couleurs (semi-)transparentes en dehors de la zone ciblée.
	# 	if operation['tool_id'] != self.id:
	# 		return
	# 	if operation['path'] is None:
	# 		return
	# 	self.restore_pixbuf()
	# 	cairo_context = cairo.Context(self.get_surface())
	# 	rgba = operation['rgba']
	# 	old_rgba = operation['old_rgba']
	# 	cairo_context.set_source_rgba(255, 255, 255, 1.0)
	# 	cairo_context.append_path(operation['path'])
	# 	cairo_context.set_operator(cairo.Operator.DEST_IN)
	# 	cairo_context.fill_preserve()

	# 	self.get_image().temp_pixbuf = Gdk.pixbuf_get_from_surface(self.get_surface(), \
	# 		0, 0, self.get_surface().get_width(), self.get_surface().get_height())

	# 	tolerance = 10
	# 	i = -1 * tolerance
	# 	while i < tolerance:
	# 		red = max(0, old_rgba[0]+i)
	# 		green = max(0, old_rgba[1]+i)
	# 		blue = max(0, old_rgba[2]+i)
	# 		red = int( min(255, red) )
	# 		green = int( min(255, green) )
	# 		blue = int( min(255, blue) )
	# 		self.get_image().temp_pixbuf = self.get_image().temp_pixbuf.add_alpha(True, red, green, blue)
	# 		i = i+1
	# 	self.restore_pixbuf()
	# 	cairo_context2 = cairo.Context(self.get_surface())

	# 	cairo_context2.append_path(operation['path'])
	# 	cairo_context2.set_operator(cairo.Operator.CLEAR)
	# 	cairo_context2.set_source_rgba(255, 255, 255, 1.0)
	# 	cairo_context2.fill()
	# 	cairo_context2.set_operator(cairo.Operator.OVER)

	# 	Gdk.cairo_set_source_pixbuf(cairo_context2, \
	# 		self.get_image().get_temp_pixbuf(), 0, 0)
	# 	cairo_context2.append_path(operation['path'])
	# 	cairo_context2.paint()
	# 	self.non_destructive_show_modif()
	# 	cairo_context2.set_operator(cairo.Operator.DEST_OVER)
	# 	cairo_context2.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)
	# 	cairo_context2.paint()

	def do_tool_operation(self, operation):
		if operation['tool_id'] != self.id:
			return
		if operation['path'] is None:
			return
		self.restore_pixbuf()
		w_context = cairo.Context(self.get_surface())
		rgba = operation['rgba']
		w_context.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)
		w_context.append_path(operation['path'])
		w_context.fill()

