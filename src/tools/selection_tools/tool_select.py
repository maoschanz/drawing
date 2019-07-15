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
		self.operation_type = None # 'op-define'
		self.behavior = 'rectangle'
		self.add_tool_action_enum('selection_type', self.selected_type_id)

		# Special bottom panel TODO common to the 3 types
		# builder = Gtk.Builder.new_from_resource( \
		#                 '/com/github/maoschanz/drawing/tools/ui/tool_select.ui')
		# self.bottom_panel = builder.get_object('bottom-panel')
		# actions_menu = builder.get_object('actions-menu')
		# builder.get_object('actions_btn').set_menu_model(actions_menu)

		# self.window.bottom_panel_box.add(self.bottom_panel)
		# self.implements_panel = True

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
		# TODO tout le bazar sur has_been_used
		if not preserve_selection:
			self.unselect_and_apply()




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
		elif self.behavior == 'freehand':
			self.draw_polygon(event_x, event_y)
		elif self.behavior == 'cancel':
			self.unselect_and_apply()
			self.restore_pixbuf()
			self.non_destructive_show_modif()

	def on_motion_on_area(self, area, event, surface, event_x, event_y):
		if self.behavior == 'rectangle':
			self.build_rectangle_path(self.x_press, self.y_press, event_x, event_y)
			operation = self.build_operation()
			self.do_tool_operation(operation) # FIXME ça pousse à load race de
			# trucs inutiles vers le selection manager alors qu'on veut juste
			# dessiner un path
		elif self.behavior == 'freehand':
			self.draw_polygon(event_x, event_y)
		elif self.behavior == 'drag':
			# self.drag_to(event_x, event_y)
			pass # on modifie réellement les coordonnées, c'est pas une "vraie" preview

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
			self.apply_operation(operation)
			self.get_selection().show_popover(True)
		elif self.behavior == 'freehand':
			if self.draw_polygon(event_x, event_y):
				self.restore_pixbuf()
				self.get_selection().load_from_path(self.future_path)
				if self.selection_is_active():
					self.get_selection().show_popover(True)
					# self.set_selection_has_been_used(False) # TODO
			else:
				return # without updating the surface so the path is visible
		elif self.behavior == 'color':
			self.future_path = utilities_get_magic_path(surface, event_x, event_y, self.window, 1)
			self.operation_type = 'op-define'
			operation = self.build_operation()
			self.apply_operation(operation)
		elif self.behavior == 'drag':
			self.drag_to(event_x, event_y)

	def drag_to(self, event_x, event_y):
		x = self.get_selection().selection_x
		y = self.get_selection().selection_y
		self.future_x = x + event_x - self.x_press
		self.future_y = y + event_y - self.y_press
		self.operation_type = 'op-drag'
		operation = self.build_operation()
		self.do_tool_operation(operation)
		self.operation_type = 'op-define'

	############################################################################
	# Path management ##########################################################

	def draw_polygon(self, event_x, event_y):
		"""This method is specific to the 'free selection' mode."""
		cairo_context = cairo.Context(self.get_surface())
		cairo_context.set_source_rgba(0.5, 0.5, 0.5, 0.5)
		cairo_context.set_dash([3, 3])
		if self.future_path is None:
			self.closing_x = event_x
			self.closing_y = event_y
			cairo_context.move_to(event_x, event_y)
			self.future_path = cairo_context.copy_path()
			return False
		if (max(event_x, self.closing_x) - min(event_x, self.closing_x) < self.closing_precision) \
		and (max(event_y, self.closing_y) - min(event_y, self.closing_y) < self.closing_precision):
			cairo_context.append_path(self.future_path)
			cairo_context.close_path()
			cairo_context.stroke_preserve()
			self.future_path = cairo_context.copy_path()
			return True
		else:
			cairo_context.append_path(self.future_path)
			cairo_context.line_to(int(event_x), int(event_y))
			cairo_context.stroke_preserve() # draw the line without closing the path
			self.future_path = cairo_context.copy_path()
			self.non_destructive_show_modif() # XXX
			return False

	def tool_select_all(self):
		self.build_rectangle_path(0, 0, self.get_main_pixbuf().get_width(), \
		                                    self.get_main_pixbuf().get_height())
		self.operation_type = 'op-define'
		operation = self.build_operation()
		self.do_tool_operation(operation)
		self.get_selection().show_popover(True)

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

	def delete_selection(self):
		self.operation_type = 'op-delete'
		operation = self.build_operation()
		self.apply_operation(operation)
		self.operation_type = 'op-define'

	def import_selection(self, pixbuf):
		self.future_pixbuf = pixbuf
		self.operation_type = 'op-import'
		operation = self.build_operation()
		self.apply_operation(operation)
		self.operation_type = 'op-define'

	def unselect_and_apply(self):
		if self.operation_type is None:
			return
		self.operation_type = 'op-apply'
		operation = self.build_operation()
		self.apply_operation(operation)
		self.operation_type = 'op-define'
		self.cursor_name = 'cross'
		self.window.set_cursor(True)
		self.get_selection().reset()
		self.future_path = None

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
		# print('drag to : ', operation['pixb_x'], operation['pixb_y'])
		self.get_selection().selection_x = operation['pixb_x']
		self.get_selection().selection_y = operation['pixb_y']
		self.non_destructive_show_modif()

	def op_define(self, operation):
		if operation['initial_path'] is None:
			return
		self.get_selection().selection_x = operation['pixb_x']
		self.get_selection().selection_y = operation['pixb_y']
		self.get_selection().temp_x = operation['pixb_x']
		self.get_selection().temp_y = operation['pixb_y']
		self.get_selection().load_from_path(operation['initial_path'])

	def op_apply(self):
		cairo_context = cairo.Context(self.get_surface())
		self.get_selection().apply_selection_to_surface(cairo_context, False)

	############################################################################
	# Operations management implementations ####################################

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
			self.get_selection().reset() # the selection is reset here because
			                          # op_delete is also used for the 'op-drag'
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
			# Opération instantanée correspondant à l'aperçu de l'op-drag, donc
			# la définition d'une sélection (rectangulaire ou non) par
			# construction d'un path qui sera "fusionné" au main_pixbuf.
			# On modifie les coordonnées connues du selection_manager.
			if self.get_selection_pixbuf() is None:
				return
			self.op_delete(operation)
			self.op_drag(operation)
			self.op_apply()

################################################################################

