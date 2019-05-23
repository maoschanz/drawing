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
		self.selected_type_id = 'rectangle'
		self.selected_type_label = _("Rectangle selection")
		self.background_type_id = 'transparent'
		self.temp_path = None
		self.temp_x = 0
		self.temp_y = 0
		self.closing_x = 0
		self.closing_y = 0

		self.add_tool_action_simple('selection_cut', self.action_cut)
		self.add_tool_action_simple('selection_copy', self.action_copy)
		self.add_tool_action_simple('selection_delete', self.action_selection_delete)

		# self.add_tool_action_simple('selection_crop', self.action_selection_crop)
		# self.add_tool_action_simple('selection_scale', self.action_selection_scale)
		# self.add_tool_action_simple('selection_flip', self.action_selection_flip)
		# self.add_tool_action_simple('selection_rotate', self.action_selection_rotate)
		# self.add_tool_action_simple('selection_saturate', self.action_selection_saturate)

		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/drawing/tools/ui/tool_select.ui')

		menu_r = builder.get_object('right-click-menu')
		self.rightc_popover = Gtk.Popover.new_from_model(self.window.notebook, menu_r)
		menu_l = builder.get_object('left-click-menu')
		self.selection_popover = Gtk.Popover.new_from_model(self.window.notebook, menu_l)

		self.add_tool_action_enum('selection_type', self.selected_type_id)

		self.selection_has_been_used = False
		# self.selection_is_active = False
		# self.reset_temp()

	def on_tool_selected(self):
		self.selection_has_been_used = True
		self.update_actions_state()
		self.selection_popover.set_relative_to(self.get_image())
		self.update_surface()

	def on_tool_unselected(self):
		self.set_actions_state(False)

	def selection_is_active(self): # XXX
		return self.get_image().selection_is_active

	def update_actions_state(self):
		if self.selection_is_active():
			self.cursor_name = 'grab'
		else:
			self.cursor_name = 'cross'
		self.set_actions_state(self.selection_is_active())

	def set_actions_state(self, state): # XXX du coup non puisque c'est valable à l'échelle de l'image
		self.set_action_sensitivity('unselect', state)
		self.set_action_sensitivity('selection_cut', state)
		self.set_action_sensitivity('selection_copy', state)
		self.set_action_sensitivity('selection_delete', state)
		self.set_action_sensitivity('selection_export', state)
		self.set_action_sensitivity('new_tab_selection', state)

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
		# return self.selected_type_label # XXX better ?

	def get_edition_status(self):
		self.set_active_type()
		label = self.selected_type_label
		if self.selection_is_active():
			label = label + ' - ' +  _("Drag the selection or right-click on the canvas")
		else:
			label = label + ' - ' +  _("Select an area or right-click on the canvas")
		return label

	############################################################################

	def give_back_control(self): # FIXME la plupart de ces trucs ça va dans image hein
		if self.selection_has_been_used:
			self.apply_selection()
			self.get_image().forget_selection()
			self.get_image().reset_temp()
			return False
		else:
			self.selection_has_been_used = True # XXX ???
			self.get_image().forget_selection()
			return self.cancel_ongoing_operation()

	def apply_selection(self):
		if self.selection_is_active():
			operation = self.build_operation()
			self.apply_operation(operation)

	def cancel_ongoing_operation(self):
		self.get_image().reset_temp()
		self.restore_pixbuf()
		self.non_destructive_show_modif()
		self.selection_has_been_used = False
		return True

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

	def on_press_on_area(self, area, event, surface, tool_width, lc, rc, event_x, event_y):
		self.x_press = event_x
		self.y_press = event_y
		behavior = self.get_press_behavior()
		if behavior == 'grab-selection':
			self.cursor_name = 'grabbing'
			self.window.set_cursor(True)
		if behavior == 'select-color':
			self.get_image().selection_path = utilities_get_magic_path(surface, \
				event_x, event_y, self.window, 1)
		elif behavior == 'begin-freehand':
			self.get_image().init_path(event_x, event_y)
		if not self.get_image().point_is_in_selection(self.x_press, self.y_press):
			self.cursor_name = 'cross'
			self.window.set_cursor(True)
			self.give_back_control()
			self.restore_pixbuf()
			self.non_destructive_show_modif()
		if behavior == 'select-rectangle':
			self.get_image().init_path(event_x, event_y)

	def on_motion_on_area(self, area, event, surface, event_x, event_y):
		if self.selection_is_active():
			pass
			# self.update_surface() # XXX inutile pour le moment car on n'update pas
			# du tout selection_x et selection_y TODO
		else:
			if self.selected_type_id == 'freehand':
				self.restore_pixbuf()
				self.get_image().draw_polygon(event_x, event_y)

	def on_unclicked_motion_on_area(self, event, surface):
		if not self.selection_is_active():
			self.cursor_name = 'cross'
		elif self.get_image().point_is_in_selection(event.x, event.y):
			self.cursor_name = 'grab'
		else:
			self.cursor_name = 'cross'
		self.window.set_cursor(True)

	def set_rightc_popover_position(self, x, y):
		rectangle = Gdk.Rectangle()
		rectangle.x = int(x)
		rectangle.y = int(y)
		rectangle.height = 1
		rectangle.width = 1
		self.rightc_popover.set_pointing_to(rectangle)
		self.rightc_popover.set_relative_to(self.get_image())

	def get_release_behavior(self):
		if not self.selection_is_active():
			return self.selected_type_id
		elif self.get_image().point_is_in_selection(self.x_press, self.y_press):
			return 'drag-selection'
		else:
			return 'cancel'

	def on_release_on_area(self, area, event, surface, event_x, event_y):
		if event.button == 3:
			self.set_rightc_popover_position(event.x, event.y)
			self.show_popover(True)
			return
		behavior = self.get_release_behavior()
		if behavior == 'rectangle': # TODO image method
			self.get_image().draw_rectangle(event_x, event_y)
			if self.selection_is_active():
				self.show_popover(True)
				self.selection_has_been_used = False
		elif behavior == 'freehand': # TODO image method
			if self.get_image().draw_polygon(event_x, event_y):
				self.restore_pixbuf()
				self.get_image().create_free_selection_from_main()
				if self.selection_is_active():
					self.show_popover(True)
					self.selection_has_been_used = False
			else:
				return # without updating the surface so the path is visible
		elif behavior == 'color': # TODO image method
			self.restore_pixbuf()
			if self.get_image().selection_path is not None:
				self.get_image().create_free_selection_from_main()
				if self.selection_is_active():
					self.show_popover(True)
					self.selection_has_been_used = False
		self.update_surface()
		if behavior == 'drag-selection':
			self.drag_to(event_x, event_y)
			self.cursor_name = 'grab'
			self.window.set_cursor(True)
			self.update_surface()
		else:
			self.restore_pixbuf()
			self.non_destructive_show_modif()

	def update_surface(self):
		operation = self.build_operation()
		self.do_tool_operation(operation)
		self.non_destructive_show_modif()

	def show_popover(self, state):
		self.selection_popover.popdown()
		self.rightc_popover.popdown()
		if self.selection_is_active() and state:
			self.set_popover_position()
			self.selection_popover.popup()
		elif state:
			self.temp_x = self.rightc_popover.get_pointing_to()[1].x
			self.temp_y = self.rightc_popover.get_pointing_to()[1].y
			self.get_image().selection_x = self.rightc_popover.get_pointing_to()[1].x
			self.get_image().selection_y = self.rightc_popover.get_pointing_to()[1].y
			self.rightc_popover.popup()

	def set_popover_position(self):
		rectangle = Gdk.Rectangle()
		main_x, main_y = self.get_image().get_main_coord()
		x = self.get_image().selection_x + self.get_selection_pixbuf().get_width()/2 - main_x
		y = self.get_image().selection_y + self.get_selection_pixbuf().get_height()/2 - main_y
		x = max(0, min(x, self.get_image().get_allocated_width()))
		y = max(0, min(y, self.get_image().get_allocated_height()))
		[rectangle.x, rectangle.y] = [x, y]
		rectangle.height = 1
		rectangle.width = 1
		self.selection_popover.set_pointing_to(rectangle)

	def drag_to(self, final_x, final_y):
		delta_x = final_x - self.x_press
		delta_y = final_y - self.y_press
		self.restore_pixbuf()
		if delta_x == 0 and delta_y == 0:
			pass
		else:
			self.selection_has_been_used = True
			self.get_image().selection_x += delta_x
			self.get_image().selection_y += delta_y
		self.non_destructive_show_modif()

	def action_cut(self, *args):
		self.copy_operation()
		self.action_selection_delete()

	def action_copy(self, *args):
		self.selection_has_been_used = True
		self.copy_operation()

	def copy_operation(self):
		cb = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
		cb.set_image(self.get_selection_pixbuf())

	def action_selection_delete(self, *args):
		self.selection_has_been_used = True
		self.restore_pixbuf()
		self.delete_temp()
		self.reset_temp()
		self.apply_to_pixbuf() # actually needed

	# def action_selection_flip(self, *args):
	# 	self.try_edit('flip')

	# def action_selection_scale(self, *args):
	# 	self.try_edit('scale')

	# def action_selection_crop(self, *args):
	# 	self.try_edit('crop')

	# def action_selection_saturate(self, *args):
	# 	self.try_edit('saturate')

	# def action_selection_rotate(self, *args):
	# 	self.try_edit('rotate')

	# def try_edit(self, tool_id):
	# 	if self.selection_is_active:
	# 		self.window.hijack_begin(self.id, tool_id)
	# 	else:
	# 		self.window.tools[tool_id].row.set_active(True)

	############################################################################

	# def on_confirm_hijacked_modif(self):  # FIXME IMAGE.PY
	# 	self.selection_has_been_used = True
	# 	self.window.hijack_end()
	#	self.create_selection_from_arbitrary_pixbuf(False)

	############################################################################

	def build_operation(self):
		if self.get_image().get_selection_pixbuf() is None:
			pixbuf = None
		else:
			pixbuf = self.get_image().get_selection_pixbuf().copy()
		operation = {
			'tool_id': self.id,
			'initial_path': self.temp_path,
			'pixbuf': pixbuf,
			'pixb_x': self.get_image().selection_x,
			'pixb_y': self.get_image().selection_y
		}
		return operation

	def do_tool_operation(self, operation):
		if operation['tool_id'] != self.id:
			return
		self.restore_pixbuf()
		self.get_image().update_history_sensitivity(True)
		if operation['initial_path'] is not None:
			cairo_context = cairo.Context(self.get_surface())
			cairo_context.new_path()
			cairo_context.append_path(operation['initial_path'])
			cairo_context.clip()
			cairo_context.set_operator(cairo.Operator.CLEAR)
			cairo_context.paint()
			cairo_context.set_operator(cairo.Operator.OVER)
		if operation['pixbuf'] is not None:
			cairo_context2 = cairo.Context(self.get_surface())
			Gdk.cairo_set_source_pixbuf(cairo_context2, operation['pixbuf'],
				operation['pixb_x'], operation['pixb_y'])
			cairo_context2.paint()

