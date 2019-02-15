# tool_replace.py XXX still shit

from gi.repository import Gtk, Gdk, Gio, GdkPixbuf
import cairo

from .tools import ToolTemplate
from .utilities import utilities_get_rgb_for_xy

class ToolReplace(ToolTemplate):
	__gtype_name__ = 'ToolReplace'

	implements_panel = False

	def __init__(self, window, **kwargs):
		super().__init__('replace', _("Replace color"), 'edit-delete-symbolic', window, False)
		self.new_color = None
		self.old_color = None
		self.use_size = True

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color, event_x, event_y):
		if event.button == 1:
			self.new_color = left_color
		else:
			self.new_color = right_color
		self.tool_width = tool_width

	def on_release_on_area(self, area, event, surface, event_x, event_y):
		self.old_color = utilities_get_rgb_for_xy(surface, event.x, event.y)
		i = -1 * self.tool_width
		while i < self.tool_width:
			red = max(0, self.old_color[0]+i)
			green = max(0, self.old_color[1]+i)
			blue = max(0, self.old_color[2]+i)
			red = int( min(255, red) )
			green = int( min(255, green) )
			blue = int( min(255, blue) )
			temporary_pixbuf = self.get_main_pixbuf().add_alpha(True, red, green, blue)
			self.get_image().main_pixbuf = temporary_pixbuf
			i = i+1
		self.restore_pixbuf()
		self.non_destructive_show_modif()
		w_context = cairo.Context(self.get_surface())
		w_context.set_operator(cairo.Operator.DEST_OVER)
		w_context.set_source_rgba(self.new_color.red, self.new_color.green, self.new_color.blue, self.new_color.alpha)
		w_context.paint()
		self.apply_to_pixbuf()
