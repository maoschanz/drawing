# history_manager.py
#
# Copyright 2018-2020 Romain F. T.
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

from gi.repository import Gdk, Gio, GdkPixbuf, GLib

################################################################################

class DrHistoryManager():
	__gtype_name__ = 'DrHistoryManager'

	def __init__(self, image, **kwargs):
		self._image = image

		self._undo_history = []
		self._redo_history = []
		self._is_saved = True
		# TODO

	def add_operation(self, operation):
		pass # TODO

	def can_undo(self):
		pass # TODO

	def try_undo(self):
		pass # TODO

	def can_redo(self):
		pass # TODO

	def try_redo(self):
		pass # TODO

	def try_redo(self, *args):
		operation = self._redo_history.pop()
		if operation['tool_id'] is None:
			# L'odeur de la fuite mémoire
			self.try_redo()
		else:
			self._get_tool(operation['tool_id']).apply_operation(operation)

	def _get_tool(self, tool_id):
		all_tools = self.image.window.tools
		if tool_id in all_tools:
			return all_tools[tool_id]
		else:
			# XXX throw something instead
			self.image.window.prompt_message(True, "Error: no tool " + tool_id)

	def add_save(self, pixbuf):
		pass # TODO

	############################################################################
################################################################################

