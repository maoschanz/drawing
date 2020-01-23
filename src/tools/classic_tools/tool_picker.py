# tool_picker.py

from gi.repository import Gdk

from .abstract_classic_tool import AbstractClassicTool
from .utilities_tools import utilities_get_rgba_for_xy

class ToolPicker(AbstractClassicTool):
	__gtype_name__ = 'ToolPicker'

	def __init__(self, window, **kwargs):
		super().__init__('picker', _("Color Picker"), 'color-select-symbolic', window)
		self.use_size = False

	def get_options_model(self):
		return None

	def on_release_on_area(self, event, surface, event_x, event_y):
		rgba_vals = utilities_get_rgba_for_xy(surface, event_x, event_y)
		if rgba_vals is None:
			return # click outside of the surface
		r = rgba_vals[0] / 255
		g = rgba_vals[1] / 255
		b = rgba_vals[2] / 255
		a = rgba_vals[3] / 255
		color = Gdk.RGBA(red=r, green=g, blue=b, alpha=a)
		if event.button == 1:
			self.window.options_manager.set_left_color(color)
		elif event.button == 3:
			self.window.options_manager.set_right_color(color)
		self.window.back_to_previous()

	############################################################################
################################################################################
