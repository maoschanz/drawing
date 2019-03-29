# tool_picker.py

from gi.repository import Gtk, Gdk
import cairo

from .abstract_tool import ToolTemplate
from .utilities import utilities_get_rgb_for_xy

class ToolPicker(ToolTemplate):
	__gtype_name__ = 'ToolPicker'

	implements_panel = False

	def __init__(self, window, **kwargs):
		super().__init__('picker', _("Color Picker"), 'color-select-symbolic', window, False)

	def get_options_model(self):
		return None

	def on_release_on_area(self, area, event, surface, event_x, event_y):
		rgb_vals = utilities_get_rgb_for_xy(surface, event.x, event.y)
		if rgb_vals == [-1, -1, -1]:
			return # click outside of the surface
		color = Gdk.RGBA(red=rgb_vals[0]/255, green=rgb_vals[1]/255, blue=rgb_vals[2]/255)
		color.alpha = 1.0
		if event.button == 3:
			self.window.color_popover_r.color_widget.set_rgba(color)
		elif event.button == 1:
			self.window.color_popover_l.color_widget.set_rgba(color)

		self.window.back_to_former_tool()
