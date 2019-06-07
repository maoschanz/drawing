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
		self.operation_type = 'drag' # TODO bof bof comme stratégie

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

	def update_cursor(self):
		if self.selection_is_active():
			self.cursor_name = 'grab'
		else:
			self.cursor_name = 'cross'

	def get_press_behavior(self):
		if self.selection_is_active():
			if self.get_selection().point_is_in_selection(self.x_press, self.y_press):
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
		elif self.get_selection().point_is_in_selection(self.x_press, self.y_press):
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
			self.draw_rectangle(event_x, event_y)
			if self.selection_is_active():
				self.show_popover(True)
				self.set_selection_has_been_used(False)
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
		self.update_surface()
		if behavior == 'drag-selection':
			self.drag_to(event_x, event_y)
			self.cursor_name = 'grab'
			self.window.set_cursor(True)
			self.update_surface()
		else:
			self.restore_pixbuf()
			self.non_destructive_show_modif()

	def drag_to(self, final_x, final_y):
		delta_x = final_x - self.x_press
		delta_y = final_y - self.y_press
		self.restore_pixbuf()
		if delta_x == 0 and delta_y == 0:
			pass
		else:
			self.set_selection_has_been_used(True)
			self.future_x += delta_x
			self.future_y += delta_y
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

	def tool_select_all(self):
		pass # TODO utiliser draw_rectangle

	def draw_rectangle(self, event_x, event_y): # TODO donner les 4 coordonnées en paramètre
		if self.future_path is None:
			return
		cairo_context = cairo.Context(self.get_surface())
		# cairo_context.set_source_rgba(0.5, 0.5, 0.5, 0.5)
		# cairo_context.set_dash([3, 3])
		cairo_context.append_path(self.future_path)
		press_x, press_y = cairo_context.get_current_point() # XXX pourquoi les retenir du coup ?

		x0 = int( min(press_x, event_x) )
		y0 = int( min(press_y, event_y) )
		x1 = int( max(press_x, event_x) )
		y1 = int( max(press_y, event_y) )
		w = x1 - x0
		h = y1 - y0
		if w <= 0 or h <= 0:
			self.future_path = None
			return

		self.future_x = x0
		self.future_y = y0
		# XXX la définition du pixbuf se fait mtn dans le selection_manager
		# temp_surface = Gdk.cairo_surface_create_from_pixbuf(self.get_main_pixbuf(), 0, None)
		# temp_surface = temp_surface.map_to_image(cairo.RectangleInt(x0, y0, w, h))
		# self.selection_pixbuf = Gdk.pixbuf_get_from_surface(temp_surface, \
		#               0, 0, temp_surface.get_width(), temp_surface.get_height())

		cairo_context.new_path()
		cairo_context.move_to(x0, y0)
		cairo_context.line_to(x1, y0)
		cairo_context.line_to(x1, y1)
		cairo_context.line_to(x0, y1)
		cairo_context.close_path()

		self.future_path = cairo_context.copy_path()
		# self.temp_path = cairo_context.copy_path() # XXX XXX XXX
		# self.set_temp() # XXX XXX XXX TODO






	############################################################################
	# Operations management methods ############################################

	def update_surface(self):
		operation = self.build_operation()
		self.do_tool_operation(operation)
		self.non_destructive_show_modif()

	def apply_selection(self): # XXX XXX XXX FIXME excessivement mauvais
		# if self.selection_is_active():
			operation = self.build_operation()
			self.apply_operation(operation)

	def delete_selection(self):
		self.operation_type = 'op-delete'
		self.apply_selection()
		self.operation_type = 'op-drag'

	def import_selection(self, pixbuf):
		self.get_image().selection.set_pixbuf(pixbuf, True)
		self.operation_type = 'op-import'
		self.apply_selection()
		self.operation_type = 'op-drag'

	def op_import(self, operation):
		if operation['pixbuf'] is None:
			return
		self.get_selection().selection_pixbuf = operation['pixbuf'].copy()

	def op_delete(self, operation):
		if operation['initial_path'] is None:
			return
		self.get_selection().temp_path = operation['initial_path']
		self.get_selection().delete_temp()
		# self.get_selection().reset() # attention op_delete est aussi appelé pour d'autres opérations ???

	def op_drag(self, operation):
		if operation['initial_path'] is None:
			return
		cairo_context = cairo.Context(self.get_surface())
		Gdk.cairo_set_source_pixbuf(cairo_context, operation['pixbuf'], \
		                               operation['pixb_x'], operation['pixb_y'])
		cairo_context.paint()








	############################################################################
	# Operations management implementations#####################################

	def build_operation(self):
		if self.future_pixbuf is None:
			pixbuf = None
		else:
			pixbuf = self.future_pixbuf.copy()
		operation = {
			'tool_id': self.id,
			'operation_type': self.operation_type,
			'initial_path': self.future_path,
			'pixbuf': pixbuf,
			'pixb_x': int(self.future_x),
			'pixb_y': int(self.future_y)
		}
		return operation

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



