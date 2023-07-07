# Licensed under GPL3 https://github.com/maoschanz/drawing/blob/master/LICENSE

from gi.repository import Gdk, GLib
from .history_state import DrHistoryState
# from .abstract_tool import WrongToolIdException

################################################################################

# 

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

	def get_initial_operation(self):
		return self._undo_history[-1].initial_state

	def empty_history(self):
		self._undo_history.clear()
		self._redo_history.clear()

	############################################################################
	# Controls accessed by DrImage #############################################

	def try_undo(self):
	
		if self._operation_is_ongoing():
			self._image.active_tool().cancel_ongoing_operation()
			return

		undone_op = self._undo_history[-1].pop_last_operation()
		if undone_op is not None:
			# Dont save reloads from disk to the redo_history.
			# TODO: The reason is the redo can cause some weird
			# behaviour with the undo button if it is done just 
			# after reloading. It might be able to get fixed by 
			# rethinking the try_redo method a bit.
			self._redo_history.append(undone_op)

		if self._undo_history[-1].is_empty() and len(self._undo_history) > 1:
			self._undo_history.pop()
		
		self._rebuild_from_history_async()
		self._image.update_history_sensitivity()

	def try_redo(self, *args):
		operation = self._redo_history.pop()
		self._get_tool(operation['tool_id']).apply_operation(operation)

	def can_undo(self):
		return (len(self._undo_history) > 1 or
				len(self._undo_history[0].operations) > 0 or
				self._operation_is_ongoing())

	def can_redo(self):
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
		if self._undo_history[-1].is_full():
			# TODO if there are too many pixbufs in the history, remove a few ones
			# Issue #200, needs more design because saving can change the data
			self.add_state(self._image.main_pixbuf.copy())

		self._undo_history[-1].add_operation(operation)
		self._is_saved = False
		self._image.update_title()
		

	############################################################################
	# Cached pixbufs ###########################################################

	def set_initial_operation(self, rgba_array, pixbuf, width, height):
		
		r = float(rgba_array[0])
		g = float(rgba_array[1])
		b = float(rgba_array[2])
		a = float(rgba_array[3])
		initial_operation = {
			'tool_id': None,
			'pixbuf': pixbuf,
			'rgba': Gdk.RGBA(red=r, green=g, blue=b, alpha=a),
			'width': width, 'height': height
		}
		self._undo_history.append(DrHistoryState(initial_operation))

	def add_state(self, pixbuf):
		if pixbuf is None:
			# Context: an error message
			raise Exception(_("Attempt to save an invalid state"))
		
		new_state = {
			'tool_id': None,
			'pixbuf': pixbuf,
			'width': pixbuf.get_width(),
			'height': pixbuf.get_height()
		}

		self._undo_history.append(DrHistoryState(new_state))
		self._is_saved = True

	def has_initial_pixbuf(self):
		return len(self._undo_history) > 0

	def get_last_stored_state(self):	
		return self._undo_history[-1].initial_state

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

		self._image.restore_last_state()

		x = self._undo_history[-1].operations
		self._undo_history[-1].operations = []

		for op in x:
			self._get_tool(op['tool_id']).simple_apply_operation(op)
	
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


