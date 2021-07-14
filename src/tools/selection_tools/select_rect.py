# select_rect.py
#
# Copyright 2018-2021 Romain F. T.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from .abstract_select import AbstractSelectionTool
from .utilities_overlay import utilities_show_overlay_on_context

class ToolRectSelect(AbstractSelectionTool):
	__gtype_name__ = 'ToolRectSelect'

	def __init__(self, window, **kwargs):
		super().__init__('rect_select', _("Rectangle selection"), 'tool-select-rect-symbolic', window)

	def press_define(self, event_x, event_y):
		pass

	def motion_define(self, event_x, event_y, render):
		if not render:
			return
		self._build_rectangle_path(self.x_press, self.y_press, event_x, event_y)
		self.restore_pixbuf()
		rect = self.get_selection().get_future_path()
		if rect is not None:
			ccontext = self.get_context()
			thickness = self.get_overlay_thickness()
			utilities_show_overlay_on_context(ccontext, rect, True, thickness)

	def release_define(self, surface, event_x, event_y):
		self._build_rectangle_path(self.x_press, self.y_press, event_x, event_y)
		self.operation_type = 'op-define'
		operation = self.build_operation()
		self.apply_operation(operation)
		# self.get_selection().show_popover()

	############################################################################
################################################################################
