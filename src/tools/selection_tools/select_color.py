# select_color.py
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
from .utilities_paths import utilities_get_magic_path

class ToolColorSelect(AbstractSelectionTool):
	__gtype_name__ = 'ToolColorSelect'

	def __init__(self, window, **kwargs):
		# Context: this is a tool to "magically" select an area depending on its
		# color. For example clicking on a white pixel will select the
		# surrounding area made of white pixels.
		super().__init__('color_select', _("Color selection"), 'tool-magic-symbolic', window)

	def press_define(self, event_x, event_y):
		pass

	def motion_define(self, event_x, event_y, render):
		pass

	def release_define(self, surfc, event_x, event_y):
		path = utilities_get_magic_path(surfc, event_x, event_y, self.window, 1)
		self._pre_load_path(path)
		if path is None:
			return
		self.operation_type = 'op-define'
		operation = self.build_operation()
		self.apply_operation(operation)

	############################################################################
################################################################################

