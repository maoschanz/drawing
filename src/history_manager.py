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

	def get_saved(self):
		return self._is_saved

	############################################################################
	# Controls accessed by DrImage #############################################

	def try_undo(self):
		if self._operation_is_ongoing():
			self._image.active_tool().cancel_ongoing_operation()
			return
		if len(self._undo_history) > 0:
			last_op = self._undo_history.pop()
			self._redo_history.append(last_op)
			# If the destacked operation is just a saved pixbuf, undo again
			if last_op['tool_id'] is None:
				# L'odeur de la récursion
				return self.try_undo()
		self._rebuild_from_history()

	def try_redo(self, *args):
		operation = self._redo_history.pop()
		if operation['tool_id'] is None:
			# L'odeur de la récursion
			self.try_redo()
		else:
			self._get_tool(operation['tool_id']).apply_operation(operation)

	def can_undo(self):
		# XXX never called while an operation is ongoing so that's stupid
		return (len(self._undo_history) != 0) or self._operation_is_ongoing()

	def can_redo(self):
		return len(self._redo_history) != 0

	def update_history_actions_labels(self):
		undoable_action = self._undo_history[-1:]
		redoable_action = self._redo_history[-1:]
		undo_label = None
		redo_label = None
		# TODO store/get translatable labels instead of tool_ids (issue #42)
		if self._operation_is_ongoing():
			# XXX pointless: the method is called at application of the operation
			undo_label = self._image.active_tool().tool_id
		elif len(undoable_action) > 0:
			undo_label = undoable_action[0]['tool_id']
		if len(redoable_action) > 0:
			redo_label = redoable_action[0]['tool_id']
		self._image.window.update_history_actions_labels(undo_label, redo_label)

	############################################################################
	# Serialized operations ####################################################

	def add_operation(self, operation):
		self._image.set_surface_as_stable_pixbuf()
		# print('add_operation_to_history')
		# print(operation['tool_id'])
		# if 'select' in operation['tool_id']:
		# 	print(operation['operation_type'])
		# 	print('-----------------------------------')
		self._is_saved = False
		self._undo_history.append(operation)

	############################################################################
	# Cached pixbufs ###########################################################

	def add_save(self, pixbuf):
		pass

	############################################################################
	# Other private methods ####################################################

	def _rebuild_from_history(self):
		last_save_index = -1
		self._image.restore_first_pixbuf()
		# last_save_index = self._image.restore_first_pixbuf() # TODO
		history = self._undo_history.copy()
		self._undo_history = []
		for op in history:
			if history.index(op) > last_save_index:
				self._get_tool(op['tool_id']).simple_apply_operation(op)
			else:
				self._undo_history.append(op)
		self._image.update()
		self._image.update_history_sensitivity()

	def _operation_is_ongoing(self):
		return self._image.active_tool().has_ongoing_operation()

	def _get_tool(self, tool_id):
		all_tools = self._image.window.tools
		if tool_id in all_tools:
			return all_tools[tool_id]
		else:
			# XXX throw something instead
			self._image.window.prompt_message(True, "Error: no tool " + tool_id)

	############################################################################
################################################################################


