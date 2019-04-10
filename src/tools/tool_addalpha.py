# tool_picker.py

from gi.repository import Gtk, Gdk
import cairo

from .abstract_tool import ToolTemplate
from .utilities import utilities_get_rgb_for_xy

class ToolAddAlpha(ToolTemplate):
	__gtype_name__ = 'ToolAddAlpha'

	implements_panel = False

	def __init__(self, window, **kwargs):
		super().__init__('addalpha', _("Remove color"), 'tool-addalpha-symbolic', window, False)

	def get_options_model(self):
		return None

	def on_release_on_area(self, area, event, surface, event_x, event_y):
		rgb_vals = utilities_get_rgb_for_xy(surface, event.x, event.y)
		if rgb_vals == [-1, -1, -1]:
			return # click outside of the surface
		self.get_image().main_pixbuf = self.get_main_pixbuf().add_alpha(True, \
		                                  rgb_vals[0], rgb_vals[1], rgb_vals[2])
		self.get_image().use_stable_pixbuf()
		self.get_image().queue_draw()

		# TODO history operations
		# TODO use the size as an error margin
