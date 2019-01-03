# modes.py
#
# Copyright 2018 Romain F. T.
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

from gi.repository import Gtk

class ModeTemplate():
	__gtype_name__ = 'ModeTemplate'

	def __init__(self, window):
		self.window = window

	def get_panel(self):
		return None

	def adapt_to_window_size():
		pass

	def on_tool_changed(self):
		pass

	def on_motion_on_area(self, area, event, surface):
		pass

	def on_press_on_area(self, area, event, surface):
		pass

	def on_release_on_area(self, area, event, surface):
		pass
