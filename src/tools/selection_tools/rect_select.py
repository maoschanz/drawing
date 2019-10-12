# tool_select.py

from gi.repository import Gtk, Gdk, GdkPixbuf
import cairo

from .abstract_select import AbstractSelectionTool
from .utilities import utilities_show_overlay_on_context

class ToolRectSelect(AbstractSelectionTool):
	__gtype_name__ = 'ToolRectSelect'

	def __init__(self, window, **kwargs):
		super().__init__('rect_select', _("Rectangle selection"), 'tool-select-rect-symbolic', window)

	def press_define(self, event_x, event_y):
		pass

	def motion_define(self, event_x, event_y):
		self.build_rectangle_path(self.x_press, self.y_press, event_x, event_y)
		self.restore_pixbuf()
		cairo_context = cairo.Context(self.get_surface())
		utilities_show_overlay_on_context(cairo_context, AbstractSelectionTool.future_path, True)

	def release_define(self, surface, event_x, event_y):
		self.build_rectangle_path(self.x_press, self.y_press, event_x, event_y)
		self.operation_type = 'op-define'
		operation = self.build_operation()
		self.apply_operation(operation)
		# self.get_selection().show_popover()

	############################################################################
################################################################################
