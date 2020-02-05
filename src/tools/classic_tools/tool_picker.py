# tool_picker.py

from gi.repository import Gtk, Gdk

from .abstract_tool import AbstractAbstractTool
from .utilities import utilities_get_rgb_for_xy

class ToolPicker(AbstractAbstractTool):
	__gtype_name__ = 'ToolPicker'

	def __init__(self, window, **kwargs):
		super().__init__('picker', _("Color Picker"), 'color-select-symbolic', window)

	def get_options_model(self):
		return None

	def on_release_on_area(self, event, surface, event_x, event_y):
		rgba_vals = utilities_get_rgb_for_xy(surface, event_x, event_y)
		if rgba_vals is None:
			return # click outside of the surface
		r = rgba_vals[0] / 255
		g = rgba_vals[1] / 255
		b = rgba_vals[2] / 255
		a = rgba_vals[3] / 255
		color = Gdk.RGBA(red=r, green=g, blue=b, alpha=a)
		if event.button == 3:
			self.window.color_popover_r.color_widget.set_rgba(color)
		elif event.button == 1:
			self.window.color_popover_l.color_widget.set_rgba(color)

		self.window.back_to_previous()

	############################################################################
################################################################################
