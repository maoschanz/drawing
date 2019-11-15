# tool_picker.py

from gi.repository import Gtk, Gdk

from .abstract_classic_tool import AbstractClassicTool
from .utilities_tools import utilities_get_rgb_for_xy

class ToolPicker(AbstractClassicTool):
	__gtype_name__ = 'ToolPicker'

	def __init__(self, window, **kwargs):
		super().__init__('picker', _("Color Picker"), 'color-select-symbolic', window)
		# self.use_color = False

	def get_options_model(self):
		return None

	def on_release_on_area(self, event, surface, event_x, event_y):
		rgb_vals = utilities_get_rgb_for_xy(surface, event_x, event_y)
		if rgb_vals == [-1, -1, -1]:
			return # click outside of the surface
		color = Gdk.RGBA(red=rgb_vals[0]/255, green=rgb_vals[1]/255, blue=rgb_vals[2]/255)
		color.alpha = 1.0
		if event.button == 1:
			self.window.options_manager.set_left_color(color)
		elif event.button == 3:
			self.window.options_manager.set_right_color(color)
		self.window.back_to_previous()
