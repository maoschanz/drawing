# tool_paint.py XXX still shit

from gi.repository import Gtk, Gdk, GdkPixbuf
import cairo

from .tools import ToolTemplate
from .utilities import utilities_get_magic_path

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
		self.magic_path = utilities_get_magic_path(surface, x, y, self.window)

		operation = self.build_operation()
		self.apply_operation(operation)

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'rgba': self.new_color,
			'path': self.magic_path
		}
		return operation

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
