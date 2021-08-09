# abstract_select.py
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

import cairo
from gi.repository import Gtk
from .abstract_tool import AbstractAbstractTool
from .optionsbar_selection import OptionsBarSelection
from .utilities_overlay import utilities_show_overlay_on_context
from .selection_manager import NoSelectionPixbufException

class AbstractSelectionTool(AbstractAbstractTool):
	__gtype_name__ = 'AbstractSelectionTool'

	def __init__(self, tool_id, label, icon_name, window, **kwargs):
		super().__init__(tool_id, label, icon_name, window)
		self.menu_id = 2
		self.accept_selection = True

		self._future_pixbuf = None
		self.x_press = 0
		self.y_press = 0
		self.local_dx = 0
		self.local_dy = 0
		self.operation_type = None # 'op-define'

		self.load_tool_action_enum('selection-color', 'last-delete-replace')
		self.add_tool_action_boolean('selection-extract', False)

	############################################################################
	# UI implementations #######################################################

	def get_options_label(self):
		return _("Selection options")

	def get_edition_status(self):
		if self.selection_is_active():
			label = _("Drag the selection or right-click on the canvas")
		else:
			label = _("Select an area or right-click on the canvas")
		return label

	def get_options_model(self):
		builder = Gtk.Builder.new_from_resource(self.UI_PATH + 'selection.ui')
		return builder.get_object('options-menu')

	def try_build_pane(self):
		self.pane_id = 'selection'
		self.window.options_manager.try_add_bottom_pane(self.pane_id, self)

	def build_bottom_pane(self):
		return OptionsBarSelection(self.window)

	############################################################################
	# Lifecycle implementations ################################################

	def give_back_control(self, preserve_selection):
		self.get_selection().hide_popovers()
		# TODO if the selection hasn't been used, nothing should be applied
		if not preserve_selection:
			self.unselect_and_apply()

	# def on_tool_selected(self, *args):
	# 	pass

	# def on_tool_unselected(self, *args):
	# 	pass

	def cancel_ongoing_operation(self):
		pass # XXX really ?

	def has_ongoing_operation(self):
		return False

	############################################################################
	############################################################################

	def _get_press_behavior(self, event):
		if event.button == 3:
			return 'menu'
		elif not self.selection_is_active():
			return 'define'
		elif self.get_selection().point_is_in_selection(self.x_press, self.y_press):
			return 'drag'
		else:
			return 'cancel'

	def press_define(self, event_x, event_y):
		pass # implemented by actual tools

	def motion_define(self, event_x, event_y, render):
		pass # implemented by actual tools

	def release_define(self, surface, event_x, event_y):
		pass # implemented by actual tools

	############################################################################
	# Signal callbacks implementations #########################################

	def on_press_on_area(self, event, surface, event_x, event_y):
		self.x_press = event_x
		self.y_press = event_y
		self.behavior = self._get_press_behavior(event)
		# print('press', self.behavior)
		if self.behavior == 'drag':
			self.cursor_name = 'grabbing'
			self.window.set_cursor(True)
		elif self.behavior == 'define':
			self.press_define(event_x, event_y)
		elif self.behavior == 'cancel':
			self.unselect_and_apply()
			self.restore_pixbuf()
			self.non_destructive_show_modif()

	def on_motion_on_area(self, event, surface, event_x, event_y, render=True):
		if self.behavior == 'define':
			self.motion_define(event_x, event_y, render)
		elif render and self.behavior == 'drag':
			self._preview_drag_to(event_x, event_y)

	def _preview_drag_to(self, event_x, event_y):
		self.local_dx = event_x - self.x_press
		self.local_dy = event_y - self.y_press
		self.non_destructive_show_modif()

	def on_unclicked_motion_on_area(self, event, surface):
		x, y = self.get_image().get_event_coords(event)
		if not self.selection_is_active():
			self.cursor_name = 'cross'
		elif self.get_selection().point_is_in_selection(x, y):
			self.cursor_name = 'grab'
		else:
			self.cursor_name = 'cross'
		self.window.set_cursor(True)

	def on_release_on_area(self, event, surface, event_x, event_y):
		if event.button == 3:
			if not self.get_selection().is_active:
				self.get_selection().set_coords(True, event_x, event_y)
				# TODO je ne devrais jamais appeler cette méthode ^ ici
			self.get_selection().set_popovers_position(event.x, event.y)
			self.get_selection().show_popover()
			return
		self.restore_pixbuf()
		if self.behavior == 'define':
			self.release_define(surface, event_x, event_y)
		elif self.behavior == 'drag':
			self._apply_drag_to(event_x, event_y)

	def on_draw_above(self, area, ccontext):
		if not self.selection_is_active():
			return
		ldx = self.local_dx
		ldy = self.local_dy
		self.get_selection().show_selection_on_surface(ccontext, True, ldx, ldy)
		dragged_path = self.get_selection().get_path_with_scroll(ldx, ldy)
		# ^ Method not really use elsewhere, could it be private?
		thickness = self.get_overlay_thickness()
		utilities_show_overlay_on_context(ccontext, dragged_path, True, thickness)

	############################################################################
	# Pre-loading the selection manager with non-essential data ################

	# In the first phase of the tool execution (pre-building operations), the
	# code should never call methods from `self.get_selection().*` aside of:
	# - the getters (safe by definition)
	# - the things to show/hide popovers (no actual effect on the image)
	# - the `set_future_*` methods, which are designed to preload data whose
	# values don't have any impact on the following operations, but which should
	# stored image-wide anyway (to avoid inconsistencies when switching to other
	# tabs and then switching back, for example).
	#
	# XXX c'est faux le préchargement des coordonnées ça a un réel impact

	def _pre_load_coords(self, x, y):
		self.get_selection().set_future_coords(x, y)

	def _pre_load_path(self, path, resync_coords=True):
		self.get_selection().set_future_path(path, resync_coords)

	def _build_rectangle_path(self, press_x, press_y, release_x, release_y):
		"""Build rectangle path and pre-load it in the selection manager. This
		is used in `self.select_all` (abstract, here), and in the "rectangle
		selection" implementation."""
		# XXX could be in the selection manager?
		x0 = int( min(press_x, release_x) )
		y0 = int( min(press_y, release_y) )
		x1 = int( max(press_x, release_x) )
		y1 = int( max(press_y, release_y) )
		w = x1 - x0
		h = y1 - y0
		if w <= 0 or h <= 0:
			return
		self._pre_load_coords(x0, y0)
		cairo_context = self.get_context()
		cairo_context.new_path()
		cairo_context.move_to(x0, y0)
		cairo_context.line_to(x1, y0)
		cairo_context.line_to(x1, y1)
		cairo_context.line_to(x0, y1)
		cairo_context.close_path()
		self._pre_load_path(cairo_context.copy_path(), False)

	############################################################################
	# Operations producing methods #############################################

	def _apply_drag_to(self, event_x, event_y):
		x = self.get_selection().selection_x
		y = self.get_selection().selection_y
		fx = x + event_x - self.x_press
		fy = y + event_y - self.y_press
		self._pre_load_coords(fx, fy)

		self.operation_type = 'op-drag'
		operation = self.build_operation()
		self.do_tool_operation(operation)
		self.operation_type = 'op-define'

	def select_all(self):
		total_w = self.get_main_pixbuf().get_width()
		total_h = self.get_main_pixbuf().get_height()
		self._build_rectangle_path(0, 0, total_w, total_h)
		self.operation_type = 'op-define'
		operation = self.build_operation()
		self.apply_operation(operation)
		self.get_selection().show_popover()

	def delete_selection(self):
		self.operation_type = 'op-delete'
		operation = self.build_operation()
		self.apply_operation(operation)
		self.operation_type = 'op-define'

	def import_selection(self, pixbuf):
		self.unselect_and_apply()
		self._future_pixbuf = pixbuf
		self.operation_type = 'op-import'

		sx = self.get_selection().selection_x
		sy = self.get_selection().selection_y
		# when it's 0 and 0, it's pretty hard for the user to understand that
		# there is an active selection, but changing the coords here sucks, it
		# would be a pretty bad design, breaking the rules i've decided
		# concerning interactions with the selection manager.
		self._pre_load_coords(sx, sy)

		operation = self.build_operation()
		self.apply_operation(operation)
		self.operation_type = 'op-define'

	def replace_canvas(self):
		self.operation_type = 'op-replace-canvas'
		# XXX it's copied so many times?! ugly but seems necessary
		self._future_pixbuf = self.get_selection_pixbuf().copy()
		operation = self.build_operation()
		self.apply_operation(operation)
		self.operation_type = 'op-define'

	def invert_selection(self):
		pass # TODO

	def unselect_and_apply(self):
		# Pre-loading the coords is NEEDED because we may "unselect_and_apply" a
		# selection which was defined by a selection manager in very different
		# state, but was consumed by an "undo".
		sx = self.get_selection().selection_x
		sy = self.get_selection().selection_y
		self._pre_load_coords(sx, sy)

		self.operation_type = 'op-apply'
		operation = self.build_operation()
		self.apply_operation(operation)
		self.operation_type = 'op-define'
		self.cursor_name = 'cross'
		self.window.set_cursor(True)

	### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###

	def build_operation(self):
		"""Operation is built from the operation_type, the current tool's
		'future_pixbuf' attribute, and '_future_*' attributes from the
		selection manager that were previously set."""
		if self._future_pixbuf is None: # Usual case
			pixbuf = None
		else: # Case of importation only
			pixbuf = self._future_pixbuf.copy()
			self._future_pixbuf = None

		replacement_type = self.get_option_value('selection-color')
		# FIXME the result is questionable when there was alpha in the area...
		if replacement_type == 'initial':
			gdk_rgba = self.get_image().get_initial_rgba()
			color = [gdk_rgba.red, gdk_rgba.green, gdk_rgba.blue, gdk_rgba.alpha]
		elif replacement_type == 'secondary':
			gdk_rgba = self.window.options_manager.get_right_color()
			color = [gdk_rgba.red, gdk_rgba.green, gdk_rgba.blue, gdk_rgba.alpha]
		else: # == 'alpha':
			color = [1.0, 1.0, 1.0, 0.0]
		# XXX the replacement is performed when the selection is defined, which
		# isn't the most intuitive behaviour: if the user sees a wrong
		# replacement color and changes the value to fix his manipulation, it's
		# already too late

		operation = {
			'tool_id': self.id,
			'operation_type': self.operation_type,
			'initial_path': self.get_selection().get_future_path(),
			'replacement': color,
			'extract': self.get_option_value('selection-extract'),
			'pixbuf': pixbuf,
			'pixb_x': self.get_selection().get_future_coords()[0],
			'pixb_y': self.get_selection().get_future_coords()[1],
			'local_dx': self.local_dx,
			'local_dy': self.local_dy,
		}
		return operation

	############################################################################
	# Operations consuming methods #############################################

	def _op_import(self, op):
		if op['pixbuf'] is None:
			raise NoSelectionPixbufException()
			# XXX does it run cleanly after the "return" to the calling method?
			# (compared to a more normal return)
		self._pre_load_coords(op['pixb_x'], op['pixb_y'])
		self.get_selection().set_coords(False, op['pixb_x'], op['pixb_y'])
		self.get_selection().set_pixbuf(op['pixbuf'].copy())

	def _op_replace_canvas(self, op):
		if op['pixbuf'] is None:
			raise NoSelectionPixbufException()
		self.get_image().set_main_pixbuf(op['pixbuf'].copy())
		self.get_image().use_stable_pixbuf()
		self.get_selection().reset(True)
		self.get_selection().reset_future_data()

	def _op_clean(self, operation):
		if operation['initial_path'] is None:
			return # The user double-clicked: there is no path, and it's normal
		cairo_context = self.get_context()
		cairo_context.new_path()
		cairo_context.append_path(operation['initial_path'])
		replacement_rgba = operation['replacement']
		cairo_context.set_operator(cairo.Operator.SOURCE)
		cairo_context.set_source_rgba(*replacement_rgba)
		cairo_context.fill()
		cairo_context.set_operator(cairo.Operator.OVER)

	def _op_drag(self, op):
		# print("drag to :", op['pixb_x'], op['pixb_y'])
		self.get_selection().set_coords(False, op['pixb_x'], op['pixb_y'])
		self.non_destructive_show_modif()

	def _op_define(self, op):
		if op['initial_path'] is None:
			return # The user double-clicked: there is no path, and it's normal
		self.get_selection().set_coords(True, op['pixb_x'], op['pixb_y'])
		if op['extract']:
			replacement = op['replacement']
		else:
			replacement = None
		self.get_selection().load_from_path(op['initial_path'], replacement)

	def _op_apply(self, operation):
		cairo_context = self.get_context()
		self.get_selection().show_selection_on_surface(cairo_context, False, \
		                           operation['local_dx'], operation['local_dy'])
		self.get_selection().reset(True)
		self.get_selection().reset_future_data()

	### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###

	def do_tool_operation(self, operation):
		self.start_tool_operation(operation)
		# print('operation_type', operation['operation_type'])
		if operation['operation_type'] == 'op-delete':
			# Opération instantanée (sans preview), correspondant à une action
			# de type "clic-droit > couper" ou "clic-droit > supprimer".
			# On réinitialise le selection_manager.
			self.get_selection().reset(True)
		elif operation['operation_type'] == 'op-import':
			# Opération instantanée (sans preview), correspondant à une action
			# de type "clic-droit > importer" ou "clic-droit > coller".
			# On charge un pixbuf dans le selection_manager.
			self._op_import(operation)
		elif operation['operation_type'] == 'op-replace-canvas':
			# TODO commentaire
			self._op_replace_canvas(operation)
		elif operation['operation_type'] == 'op-define':
			# Opération instantanée (sans preview), correspondant à une
			# sélection (rectangulaire ou non) par définition d'un path.
			# On charge un pixbuf dans le selection_manager.
			self._op_define(operation)
			self._op_clean(operation)
		elif operation['operation_type'] == 'op-drag':
			# Prévisualisation d'opération, correspondant à la définition d'une
			# sélection (rectangulaire ou non) par construction d'un path.
			# On modifie les coordonnées connues du selection_manager.
			self.local_dx = 0
			self.local_dy = 0
			self._op_drag(operation)
		elif operation['operation_type'] == 'op-apply':
			# Opération instantanée correspondant à l'aperçu de l'op-drag, donc
			# la définition d'une sélection (rectangulaire ou non) par
			# construction d'un path qui sera "fusionné" au main_pixbuf.
			# On modifie les coordonnées connues du selection_manager.
			if self.get_selection_pixbuf() is None:
				return
			self._op_drag(operation)
			self._op_apply(operation)

	############################################################################
################################################################################

