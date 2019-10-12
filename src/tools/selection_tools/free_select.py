# tool_select.py

from gi.repository import Gtk, Gdk, GdkPixbuf
import cairo

from .abstract_select import AbstractSelectionTool

class ToolFreeSelect(AbstractSelectionTool):
	__gtype_name__ = 'ToolFreeSelect'

	def __init__(self, window, **kwargs):
		super().__init__('free_select', _("Free selection"), 'tool-select-free-symbolic', window)
		self.closing_precision = 10
		self.closing_x = 0.0
		self.closing_y = 0.0

	def press_define(self, event_x, event_y):
		self.draw_polygon(event_x, event_y)

	def motion_define(self, event_x, event_y):
		self.draw_polygon(event_x, event_y)

	def release_define(self, surface, event_x, event_y):
		if self.draw_polygon(event_x, event_y):
			self.restore_pixbuf()
			self.operation_type = 'op-define'
			self.set_future_coords_for_free_path()
			operation = self.build_operation()
			self.apply_operation(operation)
			# self.get_selection().show_popover()
			# self.set_selection_has_been_used(False) # TODO
		else:
			return # without updating the surface so the path is visible

	############################################################################

	def draw_polygon(self, event_x, event_y):
		"""This method is specific to the 'free selection' mode."""
		cairo_context = cairo.Context(self.get_surface())
		cairo_context.set_source_rgba(0.5, 0.5, 0.5, 0.5)
		cairo_context.set_dash([3, 3])
		if AbstractSelectionTool.future_path is None:
			self.closing_x = event_x
			self.closing_y = event_y
			cairo_context.move_to(event_x, event_y)
			AbstractSelectionTool.future_path = cairo_context.copy_path()
			return False
		delta_x = max(event_x, self.closing_x) - min(event_x, self.closing_x)
		delta_y = max(event_y, self.closing_y) - min(event_y, self.closing_y)
		if (delta_x < self.closing_precision) and (delta_y < self.closing_precision):
			cairo_context.append_path(AbstractSelectionTool.future_path)
			cairo_context.close_path()
			cairo_context.stroke_preserve()
			AbstractSelectionTool.future_path = cairo_context.copy_path()
			return True
		else:
			cairo_context.append_path(AbstractSelectionTool.future_path)
			cairo_context.line_to(int(event_x), int(event_y))
			cairo_context.stroke_preserve() # draw the line without closing the path
			AbstractSelectionTool.future_path = cairo_context.copy_path()
			self.non_destructive_show_modif() # XXX
			return False

	############################################################################
################################################################################
