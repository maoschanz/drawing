# Licensed under GPL3 https://github.com/maoschanz/drawing/blob/master/LICENSE

from gi.repository import Gdk, Gio, GdkPixbuf, GLib
# from .abstract_tool import WrongToolIdException

################################################################################

class DrHistoryManager():
	__gtype_name__ = 'DrHistoryManager'

	def __init__(self, image, **kwargs):
		self._image = image

		self._undo_history = []
		self._redo_history = []
		self._is_saved = True
		self._waiting_for_rebuild = False

	def get_saved(self):
		# XXX undoing/redoing doesn't update the title so the "*" isn't visible
		# in all situations around a saving
		return self._is_saved

	def empty_history(self):
		"""Probably useless way to explicitly 'forget' the objects. It doesn't
		really free the memory, but it kinda helps i suppose."""
		for op in self._undo_history:
			self._delete_operation(op)
		for op in self._redo_history:
			self._delete_operation(op)
		self._delete_operation(self.initial_operation)

	def _delete_operation(self, op):
		for key in op:
			op[key] = None
		op = {}
		op = None

	############################################################################
	# Controls accessed by DrImage #############################################

	def try_undo(self):
		if self._operation_is_ongoing():
			self._image.active_tool().cancel_ongoing_operation()
			return
		if len(self._undo_history) > 0:
			last_op = self._undo_history.pop()
			self._redo_history.append(last_op)
		self._rebuild_from_history_async()
		self._image.update_history_sensitivity()

	def try_redo(self, *args):
		operation = self._redo_history.pop()
		if operation['tool_id'] is None:
			self._undo_history.append(operation)
			self._image.restore_last_state()
		else:
			self._get_tool(operation['tool_id']).apply_operation(operation)

	def can_undo(self):
		# XXX incorrect si ya des states et qu'on redo
		return (len(self._undo_history) > 0) or self._operation_is_ongoing()

	def can_redo(self):
		# XXX incorrect si ya des states ?
		return len(self._redo_history) > 0

#	def update_history_actions_labels(self):
#		"""Update the current decoration manager "undo/redo" labels (tooltips,
#		menuitems, etc.) to fit the current content of the history."""
#		# l'appel est commenté aussi
#		undoable_action = self._undo_history[-1:]
#		redoable_action = self._redo_history[-1:]
#		undo_label = None
#		redo_label = None
#		# TODO store/get translatable labels instead of tool_ids (issue #42),
#		# but it'll doesn't work with pixbuf states anyway…
#		if self._operation_is_ongoing():
#			# XXX pointless: the method is called after applying the operation
#			undo_label = self._image.active_tool().tool_id
#		elif len(undoable_action) > 0:
#			undo_label = undoable_action[0]['tool_id']
#		if len(redoable_action) > 0:
#			redo_label = redoable_action[0]['tool_id']
#		self._image.window.update_history_actions_labels(undo_label, redo_label)

	def rewind_history(self):
		"""Put the entire 'undo' history into the 'redo' history, so the image
		can be reset without losing any data."""
		self._redo_history = self._undo_history[::-1] + self._redo_history
		self._undo_history = []
		self._image.update_history_sensitivity()

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

	def set_initial_operation(self, rgba_array, pixbuf, width, height):
		r = float(rgba_array[0])
		g = float(rgba_array[1])
		b = float(rgba_array[2])
		a = float(rgba_array[3])
		self.initial_operation = {
			'tool_id': None,
			'pixbuf': pixbuf,
			'rgba': Gdk.RGBA(red=r, green=g, blue=b, alpha=a),
			'width': width, 'height': height
		}

	def add_state(self, pixbuf):
		if pixbuf is None:
			# Context: an error message
			raise Exception(_("Attempt to save an invalid state"))
		self._undo_history.append({
			'tool_id': None,
			'pixbuf': pixbuf,
			'width': pixbuf.get_width(),
			'height': pixbuf.get_height()
		})
		self._is_saved = True

	def has_initial_pixbuf(self):
		return self.initial_operation['pixbuf'] is not None

	def get_last_saved_state(self):
		index = self._get_last_state_index(False)
		if index == -1:
			return self.initial_operation
		else:
			return self._undo_history[index]

	def _get_last_state_index(self, allow_yeeting_states):
		"""Return the index of the last "state" operation (dict whose 'tool_id'
		value is None) in the undo-history. If there is no such operation, the
		returned index is -1 which means the only known state is the
		self.initial_operation attribute."""

		returned_index = -1
		nbPixbufs = 0
		for op in self._undo_history:
			if op['tool_id'] is None:
				last_saved_pixbuf_op = op
				returned_index = self._undo_history.index(op)
				nbPixbufs += 1

		# TODO if there are too many pixbufs in the history, remove a few ones
		# Issue #200, needs more design because saving can change the data

		# print("returned_index : " + str(returned_index))
		return returned_index

	############################################################################
	# Other private methods ####################################################

	def _rebuild_from_history_async(self):
		if not self._waiting_for_rebuild:
			# No need to duplicate calls, it will be rebuilt soon anyway
			self._waiting_for_rebuild = True
			GLib.timeout_add(500, self._rebuild_from_history, {})
		# This introduces an artificial delay of half a second, BUT in the case
		# where an user undoes several operations, i expect between 2 and 4
		# presses on ctrl+z during these 500ms, so there will be between 2 and 4
		# times less recomputation.

	def _rebuild_from_history(self, async_cb_data={}):
		"""Rebuild the image according to the content of the current history.
		This is used as a GSourceFunc so it should return False."""
		if not self._waiting_for_rebuild:
			# It has already been rebuild by an other async call
			return False
		self._waiting_for_rebuild = False

		last_save_index = self._get_last_state_index(True)
		self._image.restore_last_state()
		history = self._undo_history.copy()
		self._undo_history = []
		for op in history:
			if history.index(op) > last_save_index:
				# print("do", op['tool_id'])
				self._get_tool(op['tool_id']).simple_apply_operation(op)
			else:
				# print("skip", op['tool_id'])
				self._undo_history.append(op)
		self._image.update()
		return False

	def _operation_is_ongoing(self):
		return self._image.active_tool().has_ongoing_operation()

	def _get_tool(self, tool_id):
		all_tools = self._image.window.tools
		if tool_id in all_tools:
			return all_tools[tool_id]
		else:
			self._image.window.reveal_action_report(_("Error: no tool '%s'" % tool_id))
			# no raise: this may happen normally if last_save_index is incorrect

	############################################################################
################################################################################


