# tool_select.py

from gi.repository import Gtk, Gdk, GdkPixbuf
import cairo

from .abstract_select import AbstractSelectionTool

class ToolRectSelect(AbstractSelectionTool):
	__gtype_name__ = 'ToolRectSelect'

	def __init__(self, window, **kwargs):
		super().__init__('rect_select', _("Rectangle selection"), 'tool-select-symbolic', window)

	def press_define(self, event_x, event_y):
		pass

	def motion_define(self, event_x, event_y):
		self.build_rectangle_path(self.x_press, self.y_press, event_x, event_y)
		operation = self.build_operation()
		self.do_tool_operation(operation) # FIXME ça pousse à load race de
		# trucs inutiles vers le selection manager alors qu'on veut juste
		# dessiner un path

	def release_define(self, surface, event_x, event_y):
		self.build_rectangle_path(self.x_press, self.y_press, event_x, event_y)
		self.operation_type = 'op-define'
		operation = self.build_operation()
		self.apply_operation(operation)
		# self.get_selection().show_popover(True)
