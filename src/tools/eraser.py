# eraser.py

from gi.repository import Gtk, Gdk, Gio
import cairo

from .tools import ToolTemplate

class ToolEraser(ToolTemplate):
	__gtype_name__ = 'ToolEraser'

	use_size = True

	def __init__(self, window, **kwargs):
		super().__init__('eraser', _("Eraser"), 'edit-delete-symbolic', window)
		self.past_x = -1
		self.past_y = -1
		self.w_context = None

	def on_motion_on_area(self, area, event, surface):
		self.w_context.set_line_cap(cairo.LineCap.ROUND)
		self.w_context.set_line_width(self.tool_width)
		if (self.past_x > 0):
			self.w_context.move_to(self.past_x, self.past_y)
		self.w_context.line_to(event.x, event.y)
		self.past_x = event.x
		self.past_y = event.y
		self.w_context.stroke()

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color):
		self.tool_width = tool_width
		self.w_context = cairo.Context(surface)
		self.w_context.set_operator(cairo.Operator.CLEAR)

	def on_release_on_area(self, area, event, surface):
		self.past_x = -1
		self.past_y = -1
		self.w_context.set_operator(cairo.Operator.OVER)
		self.apply_to_pixbuf()

