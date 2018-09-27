# crop.py

from gi.repository import Gtk, Gdk, Gio
import cairo

from .tools import ToolTemplate

class ToolCrop(ToolTemplate):
	__gtype_name__ = 'ToolCrop'

	id = 'crop'
	icon_name = 'edit-select-all-symbolic'
	label = _("Crop")

	def __init__(self, window, **kwargs):
		super().__init__(window)

	def give_back_control(self):
		pass

	def on_key_on_area(self, area, event, surface):
		print("key")

	def on_motion_on_area(self, area, event, surface):
		pass

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color):
		self.window_can_take_back_control = False
		self.x_press = event.x
		self.y_press = event.y

	def on_release_on_area(self, area, event, surface):
		x0 = min(self.x_press, event.x)
		y0 = min(self.y_press, event.y)
		w = abs(self.x_press - event.x)
		h = abs(self.y_press - event.y)
		self.window.resize_surface(x0, y0, w, h)
		self.window_can_take_back_control = True
