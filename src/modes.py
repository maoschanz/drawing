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

	def get_edition_status(self):
		return '…'

	def adapt_to_window_size(self):
		pass

	def on_mode_selected(self, *args):
		pass

	def on_apply_mode(self):
		pass

	def on_cancel_mode(self):
		pass

	def on_tool_changed(self):
		pass

	def add_mode_action_simple(self, action_name, callback):
		self.window.add_action_simple(action_name, callback)

	def add_mode_action_boolean(self, action_name, default, callback):
		self.window.add_action_boolean(action_name, default, callback)

	def add_mode_action_enum(self, action_name, default, callback):
		self.window.add_action_enum(action_name, default, callback)

	def on_motion_on_area(self, area, event, surface):
		pass

	def on_press_on_area(self, area, event, surface):
		pass

	def on_release_on_area(self, area, event, surface):
		pass
