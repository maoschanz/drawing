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

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color, event_x, event_y):
		self.tool_width = tool_width

	def on_release_on_area(self, area, event, surface, event_x, event_y):
		self.rgb_vals = utilities_get_rgb_for_xy(surface, event.x, event.y)
		if self.rgb_vals == [-1, -1, -1]:
			return # click outside of the surface
		operation = self.build_operation()
		self.apply_operation(operation)

	def build_operation(self):
		margin = 0
		if False: # TODO as option
			margin = int(self.tool_width)
		operation = {
			'tool_id': self.id,
			'r': self.rgb_vals[0],
			'g': self.rgb_vals[1],
			'b': self.rgb_vals[2],
			'margin': margin
		}
		return operation

	def do_tool_operation(self, operation):
		if operation['tool_id'] != self.id:
			return
		self.restore_pixbuf()
		r0 = operation['r']
		g0 = operation['g']
		b0 = operation['b']
		for i in range(-1 * operation['margin'], operation['margin']+1):
			r = r0 + i
			if r <= 255 and r >= 0:
				for j in range(-1 * operation['margin'], operation['margin']+1):
					g = g0 + j
					if g <= 255 and g >= 0:
						for k in range(-1 * operation['margin'], operation['margin']+1):
							b = b0 + k
							if b <= 255 and b >= 0:
								self.get_image().main_pixbuf = \
								 self.get_main_pixbuf().add_alpha(True, r, g, b)
		self.get_image().use_stable_pixbuf()
		self.get_image().queue_draw()

