# tool_select.py

from gi.repository import Gtk, Gdk, GdkPixbuf
import cairo

from .abstract_tool import ToolTemplate
from .utilities import utilities_get_magic_path

class ToolSelect(ToolTemplate):
	__gtype_name__ = 'ToolSelect'

	closing_precision = 10

	def __init__(self, window, **kwargs):
		super().__init__('select', _("Selection"), 'tool-select-symbolic', window)
		self.use_color = False
		self.accept_selection = True

		self.selected_type_id = 'rectangle'
		self.selected_type_label = _("Rectangle selection")
		self.closing_x = 0
		self.closing_y = 0
		self.x_press = 0
		self.y_press = 0
		self.future_x = 0
		self.future_y = 0
		self.future_path = None
		self.future_pixbuf = None

		builder = Gtk.Builder.new_from_resource( \
		                '/com/github/maoschanz/drawing/tools/ui/tool_select.ui')

		self.add_tool_action_enum('selection_type', self.selected_type_id)

	############################################################################
	# UI implementations #######################################################

	def set_active_type(self, *args):
		selection_type = self.get_option_value('selection_type')
		if selection_type == 'rectangle':
			self.selected_type_id = 'rectangle'
			self.selected_type_label = _("Rectangle selection")
		elif selection_type == 'freehand':
			self.selected_type_id = 'freehand'
			self.selected_type_label = _("Free selection")
		else:
			self.selected_type_id = 'color'
			self.selected_type_label = _("Color selection")

	def get_options_label(self):
		return _("Selection options")

	def get_edition_status(self):
		self.set_active_type()
		label = self.selected_type_label
		if self.selection_is_active():
			label = label + ' - ' +  _("Drag the selection or right-click on the canvas")
		else:
			label = label + ' - ' +  _("Select an area or right-click on the canvas")
		return label

	############################################################################
	# Lifecycle implementations ################################################







	############################################################################
	############################################################################

	def get_press_behavior(self):
		if self.selection_is_active():
			if self.get_image().point_is_in_selection(self.x_press, self.y_press):
				return 'grab-selection'
		else:
			if self.selected_type_id == 'color':
				return 'select-color'
			elif self.selected_type_id == 'freehand':
				return 'begin-freehand'
			else:
				return 'select-rectangle'
		return 'cancel'

	def get_release_behavior(self):
		if not self.selection_is_active():
			return self.selected_type_id
		elif self.get_image().point_is_in_selection(self.x_press, self.y_press):
			return 'drag-selection'
		else:
			return 'cancel'

	############################################################################
	# Signal callbacks implementations #########################################

	def on_press_on_area(self, area, event, surface, tool_width, lc, rc, event_x, event_y):
		self.x_press = event_x
		self.y_press = event_y
		behavior = self.get_press_behavior()
		if behavior == 'grab-selection':
			self.cursor_name = 'grabbing'
			self.window.set_cursor(True)
		if behavior == 'select-color':
			self.future_path = utilities_get_magic_path(surface, event_x, event_y, self.window, 1)
		elif behavior == 'begin-freehand':
			self.init_path(event_x, event_y)
		if not self.get_selection().point_is_in_selection(self.x_press, self.y_press):
			self.cursor_name = 'cross'
			self.window.set_cursor(True)
			self.give_back_control(False) # XXX à vérifier, ça me semble louche
			self.restore_pixbuf()
			self.non_destructive_show_modif()
		if behavior == 'select-rectangle':
			self.init_path(event_x, event_y)

	def on_motion_on_area(self, area, event, surface, event_x, event_y):
		if self.selection_is_active():
			pass
			# self.update_surface() # TODO mais ça ne marchera pas à un tel simple appel mdr
		else:
			if self.selected_type_id == 'freehand':
				self.restore_pixbuf()
				self.draw_polygon(event_x, event_y)
			elif self.selected_type_id == 'rectangle':
				pass
				# TODO tracer dynamiquement le rectangle n'est pas idiot

	def on_unclicked_motion_on_area(self, event, surface):
		x = event.x + self.get_image().scroll_x
		y = event.y + self.get_image().scroll_y
		if not self.selection_is_active():
			self.cursor_name = 'cross'
		elif self.get_selection().point_is_in_selection(x, y):
			self.cursor_name = 'grab'
		else:
			self.cursor_name = 'cross'
		self.window.set_cursor(True)

	def on_release_on_area(self, area, event, surface, event_x, event_y):
		if event.button == 3:
			self.get_selection().set_r_popover_position(event.x, event.y)
			self.get_selection().show_popover(True)
			return
		behavior = self.get_release_behavior()
		# TODO TODO TODO utiliser les mêmes conditionnelles mais avec des "future_xxx"
		if behavior == 'rectangle':
			pass
			# self.draw_rectangle(event_x, event_y)
			# if self.selection_is_active():
			# 	self.show_popover(True)
			# 	self.set_selection_has_been_used(False)
		elif behavior == 'freehand':
			pass
			# if self.draw_polygon(event_x, event_y):
			# 	self.restore_pixbuf()
			# 	self.get_image().create_free_selection_from_main() # FIXME oula mdr c'est quoi mtn ça ?
			# 	if self.selection_is_active():
			# 		self.show_popover(True)
			# 		self.set_selection_has_been_used(False)
			# else:
			# 	return # without updating the surface so the path is visible
		elif behavior == 'color':
			pass
		# 	self.restore_pixbuf()
		# 	if self.future_path is not None:
		# 		self.get_image().selection.load_from_path(self.future_path)
		# 		if self.selection_is_active():
		# 			self.show_popover(True)
		# 			self.set_selection_has_been_used(False)
		# self.update_surface()
		if behavior == 'drag-selection':
			pass
			# self.drag_to(event_x, event_y)
			# self.cursor_name = 'grab'
			# self.window.set_cursor(True)
			# self.update_surface()
		else:
			self.restore_pixbuf()
			self.non_destructive_show_modif()

	############################################################################
	# Path management ##########################################################

	def init_path(self, event_x, event_y):
		"""This method moves the current path to the "press" event coordinates.
		It's used by both the 'rectangle selection' mode and the 'free
		selection' mode."""
		if self.future_path is not None:
			return
		self.closing_x = event_x
		self.closing_y = event_y
		cairo_context = cairo.Context(self.get_surface())
		cairo_context.move_to(event_x, event_y)
		self.future_path = cairo_context.copy_path()









	############################################################################
	# Operations management methods ############################################

	def op_import(self, operation):
		if operation['pixbuf'] is None:
			return
		self.get_image().selection_pixbuf = operation['pixbuf'].copy()






	############################################################################
	# Operations management implementations#####################################

	def do_tool_operation(self, operation):
		if operation['tool_id'] != self.id:
			return
		self.restore_pixbuf()
		if operation['operation_type'] == 'op-delete':
			self.op_delete(operation)
		elif operation['operation_type'] == 'op-drag':
			self.op_delete(operation)
			self.op_drag(operation)
		elif operation['operation_type'] == 'op-import':
			self.op_import(operation)
		elif operation['operation_type'] == 'op-define':
			self.op_define(operation)



