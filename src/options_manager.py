# options_manager.py
#
# Copyright 2019 Romain F. T.
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

from gi.repository import GLib
import cairo

class DrawingOptionsManager():
	__gtype_name__ = 'DrawingOptionsManager'

	def __init__(self, window):
		self.window = window

	def add_tool_option_boolean(self, name, default):
		if self.window.lookup_action(name) is not None:
			return
		self.window.add_action_boolean(name, default, self.boolean_callback)

	def add_tool_option_enum(self, name, default):
		if self.window.lookup_action(name) is not None:
			return
		self.window.add_action_enum(name, default, self.enum_callback)

	def boolean_callback(self, *args):
		new_value = not args[0].get_state()
		args[0].set_state(GLib.Variant.new_boolean(new_value))

	def enum_callback(self, *args):
		new_value = args[1].get_string()
		if new_value == args[0].get_state().get_string():
			return
		args[0].set_state(GLib.Variant.new_string(new_value))

	def get_value(self, name):
		if self.window.lookup_action(name) is None:
			return
		action = self.window.lookup_action(name)
		if action.get_state_type().dup_string() is 's':
			return action.get_state().get_string()
		else:
			return action.get_state()
