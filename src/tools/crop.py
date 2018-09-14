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
		pass

	def on_release_on_area(self, area, event, surface):
		print("crop")
