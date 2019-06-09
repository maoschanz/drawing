# tool_select.py

from gi.repository import Gtk, Gdk, GdkPixbuf
import cairo

from .abstract_tool import ToolTemplate
from .utilities import utilities_get_magic_path
from .utilities import utilities_show_overlay_on_context

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
		self.operation_type = 'op-define'
		self.behavior = 'rectangle'

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

	def give_back_control(self, preserve_selection):
		# if preserve_selection and self.selection_is_active():
		if True: # TODO
			operation = self.build_operation()
			self.apply_operation(operation)
		if not preserve_selection:
			self.get_selection().reset()






	############################################################################
	############################################################################

	def get_press_behavior(self):
		if self.selection_is_active():
			if self.get_selection().point_is_in_selection(self.x_press, self.y_press):
				return 'drag'
			#else: # superflu
			#	return 'cancel'
		else:
			if self.selected_type_id == 'color':
				return 'color'
			elif self.selected_type_id == 'freehand':
				return 'freehand'
			else:
				return 'rectangle'
		return 'cancel'

	# def get_release_behavior(self):
	# 	if not self.selection_is_active():
	# 		return self.selected_type_id
	# 	elif self.get_selection().point_is_in_selection(self.x_press, self.y_press):
	# 		return 'drag'
	# 	else:
	# 		return 'cancel'

	############################################################################
	# Signal callbacks implementations #########################################

	def on_press_on_area(self, area, event, surface, tool_width, lc, rc, event_x, event_y):
		self.x_press = event_x
		self.y_press = event_y
		self.behavior = self.get_press_behavior()
		if self.behavior == 'drag':
			self.cursor_name = 'grabbing'
			self.window.set_cursor(True)
		# elif self.behavior == 'color':
		# 	self.future_path = utilities_get_magic_path(surface, event_x, event_y, self.window, 1)
		# elif self.behavior == 'freehand':
		# 	self.init_path(event_x, event_y) # TODO
		if self.behavior == 'cancel':
		# if not self.get_selection().point_is_in_selection(self.x_press, self.y_press):
		# 	print('--------------')
		# 	print(self.behavior)
			self.operation_type = 'op-apply'
			self.cursor_name = 'cross'
			self.window.set_cursor(True)
			self.give_back_control(False) # XXX à vérifier, ça me semble louche
			self.operation_type = 'op-define'
			self.restore_pixbuf()
			self.non_destructive_show_modif()

	def on_motion_on_area(self, area, event, surface, event_x, event_y):
		if self.behavior == 'rectangle':
			self.build_rectangle_path(self.x_press, self.y_press, event_x, event_y)
			operation = self.build_operation()
			self.do_tool_operation(operation)
		elif self.behavior == 'drag':
			pass # TODO

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
		self.restore_pixbuf()
		if self.behavior == 'rectangle':
			self.build_rectangle_path(self.x_press, self.y_press, event_x, event_y)
			self.operation_type = 'op-define'
			operation = self.build_operation()
			self.do_tool_operation(operation)
		elif self.behavior == 'freehand':
			pass # TODO ?
		elif self.behavior == 'color':
			self.future_path = utilities_get_magic_path(surface, event_x, event_y, self.window, 1)
			self.operation_type = 'op-define'
			operation = self.build_operation()
			self.do_tool_operation(operation)
		elif self.behavior == 'drag':
			x = self.get_selection().selection_x
			y = self.get_selection().selection_y
			self.future_x = x + event_x - self.x_press
			self.future_y = y + event_y - self.y_press
			print('drag to : ', self.future_x, self.future_y)
			self.operation_type = 'op-drag'
			operation = self.build_operation()
			self.do_tool_operation(operation)
			self.operation_type = 'op-define'


	def drag_to(self, final_x, final_y):
		pass

	############################################################################
	# Path management ##########################################################

	def init_path(self, event_x, event_y):
		pass

	def tool_select_all(self):
		pass # TODO utiliser draw_rectangle

	def build_rectangle_path(self, press_x, press_y, release_x, release_y):
		cairo_context = cairo.Context(self.get_surface())
		x0 = int( min(press_x, release_x) )
		y0 = int( min(press_y, release_y) )
		x1 = int( max(press_x, release_x) )
		y1 = int( max(press_y, release_y) )
		w = x1 - x0
		h = y1 - y0
		if w <= 0 or h <= 0:
			self.future_path = None
			return
		self.future_x = x0
		self.future_y = y0
		cairo_context.new_path()
		cairo_context.move_to(x0, y0)
		cairo_context.line_to(x1, y0)
		cairo_context.line_to(x1, y1)
		cairo_context.line_to(x0, y1)
		cairo_context.close_path()
		self.future_path = cairo_context.copy_path()





	############################################################################
	# Operations management methods ############################################

	def update_surface(self):
		operation = self.build_operation()
		self.do_tool_operation(operation)
		self.non_destructive_show_modif()

	def apply_selection(self): # XXX FIXME mauvais
		# if self.selection_is_active():
			operation = self.build_operation()
			self.apply_operation(operation)

	def delete_selection(self):
		self.operation_type = 'op-delete'
		self.apply_selection()
		self.operation_type = 'op-define'

	def import_selection(self, pixbuf):
		self.future_pixbuf = pixbuf
		self.operation_type = 'op-import'
		self.apply_selection()
		self.operation_type = 'op-define'

	#####

	def op_import(self, operation):
		if operation['pixbuf'] is None:
			return
		self.get_selection().set_pixbuf(operation['pixbuf'].copy(), True)

	def op_delete(self, operation):
		if operation['initial_path'] is None:
			return
		self.get_selection().temp_path = operation['initial_path']
		self.get_selection().delete_temp()

	def op_drag(self, operation):
		print(operation['pixb_x'], operation['pixb_y'])
		self.get_selection().selection_x = operation['pixb_x']
		self.get_selection().selection_y = operation['pixb_y']
		self.non_destructive_show_modif()

	def op_define(self, operation):
		if operation['initial_path'] is None:
			return
		self.get_selection().selection_x = operation['pixb_x']
		self.get_selection().selection_y = operation['pixb_y']
		self.get_selection().load_from_path(operation['initial_path'])

	def op_apply(self):
		cairo_context = cairo.Context(self.get_surface())
		self.get_selection().apply_selection_to_surface(cairo_context)




	############################################################################
	# Operations management implementations#####################################

	def build_operation(self):
		if self.future_pixbuf is None: # Cas normal
			pixbuf = None
		else: # Cas des importations uniquement
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
		print(operation['operation_type'])
		if operation['operation_type'] == 'op-delete':
			# Opération instantanée (sans preview), correspondant à une action
			# de type "clic-droit > couper" ou "clic-droit > supprimer".
			# On réinitialise le selection_manager.
			self.op_delete(operation)
			self.get_selection().reset() # car op_delete est aussi appelé pour l'op-drag
		elif operation['operation_type'] == 'op-import':
			# Opération instantanée (sans preview), correspondant à une action
			# de type "clic-droit > importer" ou "clic-droit > coller".
			# On charge un pixbuf dans le selection_manager.
			self.op_import(operation)
		elif operation['operation_type'] == 'op-define':
			# Opération instantanée (sans preview), correspondant à une sélection
			# (rectangulaire ou non) par définition d'un path.
			# On charge un pixbuf dans le selection_manager.
			self.op_define(operation)
		elif operation['operation_type'] == 'op-drag':
			# Prévisualisation d'opération, correspondant à la définition d'une
			# sélection (rectangulaire ou non) par construction d'un path.
			# On modifie les coordonnées connues du selection_manager.
			self.op_delete(operation)
			self.op_drag(operation)
		elif operation['operation_type'] == 'op-apply':
			# Opération instantanée correspondant à l'aperçu de l'op-drag,
			# correspondant à la définition d'une sélection (rectangulaire ou
			# non) par construction d'un path.
			# On modifie les coordonnées connues du selection_manager.
			self.op_delete(operation)
			self.op_drag(operation)
			self.op_apply()



