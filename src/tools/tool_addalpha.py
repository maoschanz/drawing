# tool_addalpha.py

from gi.repository import Gtk, Gdk
import cairo

from .abstract_tool import ToolTemplate
from .utilities import utilities_get_rgb_for_xy

class ToolAddAlpha(ToolTemplate):
	__gtype_name__ = 'ToolAddAlpha'

	implements_panel = False

	def __init__(self, window, **kwargs):
		super().__init__('addalpha', _("Remove color"), 'tool-addalpha-symbolic', window, False)
		self.rgb_vals = []

	def get_options_model(self):
		return None

	def get_edition_status(self):
		return _("Click on an area to replace its color by transparency")

	def on_release_on_area(self, area, event, surface, event_x, event_y):
		self.rgb_vals = utilities_get_rgb_for_xy(surface, event.x, event.y)
		if self.rgb_vals == [-1, -1, -1]:
			return # click outside of the surface
		operation = self.build_operation()
		self.apply_operation(operation)

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'r': self.rgb_vals[0],
			'g': self.rgb_vals[1],
			'b': self.rgb_vals[2]
			# TODO error margin ?
		}
		return operation

	def do_tool_operation(self, operation):
		if operation['tool_id'] != self.id:
			return
		self.restore_pixbuf()
		self.get_image().main_pixbuf = self.get_main_pixbuf().add_alpha(True, \
		                         operation['r'], operation['g'], operation['b'])
		self.get_image().use_stable_pixbuf()
		self.get_image().queue_draw()
