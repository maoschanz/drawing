# select.py

from gi.repository import Gtk, Gdk, Gio, GdkPixbuf, GLib
import cairo

from .crop_dialog import DrawingCropDialog

from .tools import ToolTemplate

class ToolSelect(ToolTemplate):
	__gtype_name__ = 'ToolSelect'

	closing_precision = 10

	def __init__(self, window, **kwargs):
		super().__init__('select', _("Selection"), 'edit-select-symbolic', window)

		self.add_tool_action('unselect', self.action_unselect) # pareil que give_back_control ?
		self.add_tool_action('cut', self.action_cut)
		self.add_tool_action('copy', self.action_copy)
		self.add_tool_action('selection_delete', self.action_selection_delete)
		self.add_tool_action('selection_crop', self.action_selection_crop)
		self.add_tool_action('selection_resize', self.action_selection_resize)
		# self.add_tool_action('selection_rotate', self.action_selection_rotate)
		self.add_tool_action('selection_export', self.action_selection_export)
		self.add_tool_action('import', self.action_import)
		self.add_tool_action('paste', self.action_paste)
		self.add_tool_action('select_all', self.action_select_all)

		#############################

		self.x_press = 0.0
		self.y_press = 0.0
		self.past_x = [-1, -1]
		self.past_y = [-1, -1]
		self.selected_type_id = 'rectangle'
		self.selected_type_label = _("Rectangle")

		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/Drawing/tools/ui/select.ui')
		menu_r = builder.get_object('right-click-menu')
		self.rightc_popover = Gtk.Popover.new_from_model(self.window.drawing_area, menu_r)
		menu_l = builder.get_object('left-click-menu')
		self.selection_popover = Gtk.Popover.new_from_model(self.window.drawing_area, menu_l)

		#############################

		self.add_tool_action_enum('selection_type', self.selected_type_id, self.on_change_active_type)
		self.add_tool_action_boolean('selection_exclude', False, self.osef)

		self.selected_type_id = 'rectangle'
		self.selected_type_label = _("Rectangle")

	def on_change_active_type(self, *args):
		state_as_string = args[1].get_string()
		if state_as_string == args[0].get_state().get_string():
			return
		args[0].set_state(GLib.Variant.new_string(state_as_string))
		if state_as_string == 'rectangle':
			self.selected_type_id = 'rectangle'
			self.selected_type_label = _("Rectangle")
		else:
			self.selected_type_id = 'freehand'
			self.selected_type_label = _("Freehand")
		self.give_back_control()

	def osef(self, *args): # TODO XXX
		pass

	def get_options_model(self):
		builder = Gtk.Builder.new_from_resource("/com/github/maoschanz/Drawing/tools/ui/select.ui")
		return builder.get_object('options-menu')

	def get_options_label(self):
		return self.selected_type_label

	def give_back_control(self):
		print('selection give back control')
		if self.selection_has_been_used:
			if self.window._pixbuf_manager.selection_is_active:
				self.restore_pixbuf()
				self.window._pixbuf_manager.delete_temp()
				self.window._pixbuf_manager.show_selection_content()
				self.apply_to_pixbuf()
			self.end_selection()
			return False
		else:
			return self.cancel_ongoing_operation()

	def cancel_ongoing_operation(self):
		print('cancelito')
		self.end_selection()
		self.window._pixbuf_manager.reset_selection()
		self.show_popover(False)
		self.non_destructive_show_modif()
		return True

	def end_selection(self):
		self.show_popover(False)
		self.x_press = 0.0
		self.y_press = 0.0
		self.past_x = [-1, -1]
		self.past_y = [-1, -1]

	def show_popover(self, state):
		self.selection_popover.popdown()
		self.rightc_popover.popdown()
		if self.window._pixbuf_manager.selection_is_active and state:
			self.selection_popover.popup()
		elif state:
			self.window._pixbuf_manager.selection_x = self.rightc_popover.get_pointing_to()[1].x
			self.window._pixbuf_manager.selection_y = self.rightc_popover.get_pointing_to()[1].y
			self.rightc_popover.popup()

	# def on_motion_on_area(self, area, event, surface):
	# 	pass

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color):
		print("press")
		# area.grab_focus() # TODO ??
		self.x_press = event.x
		self.y_press = event.y
		self.left_color = left_color # TODO
		self.right_color = right_color # TODO

	def on_release_on_area(self, area, event, surface):
		print("release") # TODO à main levée c'est juste un crayon avec close_path() après
		if event.button == 3:
			rectangle = Gdk.Rectangle()
			rectangle.x = int(event.x)
			rectangle.y = int(event.y)
			rectangle.height = 1
			rectangle.width = 1
			self.rightc_popover.set_pointing_to(rectangle)
			self.rightc_popover.set_relative_to(area)
			self.show_popover(True)
			return
		elif self.selected_type_id == 'rectangle':
			# If nothing is selected (only -1), coordinates should be memorized, but
			# if something is already selected, the selection should be cancelled (the
			# action is performed outside of the current selection), or stay the same
			# (the user is moving the selection by dragging it).
			if not self.window._pixbuf_manager.selection_is_active:
				self.past_x[0] = event.x
				self.past_x[1] = self.x_press
				self.past_y[0] = event.y
				self.past_y[1] = self.y_press
				self.selection_popover.set_relative_to(area)
				self.create_selection_from_coord()
				if self.window._pixbuf_manager.selection_is_active:
					self.draw_selection_area(True)
					self.selection_has_been_used = False
			elif self.window._pixbuf_manager.point_is_in_selection(self.x_press, self.y_press):
				self.drag_to(event.x, event.y)
			else:
				self.give_back_control()
				return
		elif self.selected_type_id == 'freehand':
			if not self.window._pixbuf_manager.selection_is_active:
				print('selection is not active')
				self.selection_popover.set_relative_to(area)
				[finished, selection_path] = self.draw_polygon(event)
				if finished:
					self.restore_pixbuf()
					self.window._pixbuf_manager.create_free_selection_from_main(selection_path)
					if self.window._pixbuf_manager.selection_is_active:
						self.draw_selection_area(True)
						self.selection_has_been_used = False
					(self.x_press, self.y_press) = (-1.0, -1.0)
					self.past_x = [-1, -1]
					self.past_y = [-1, -1]
			elif self.window._pixbuf_manager.point_is_in_selection(self.x_press, self.y_press):
				self.drag_to(event.x, event.y)
			else:
				self.give_back_control()

	def get_center_of_selection(self):
		x = self.window._pixbuf_manager.selection_x + \
		self.window._pixbuf_manager.selection_pixbuf.get_width()/2
		y = self.window._pixbuf_manager.selection_y + \
		self.window._pixbuf_manager.selection_pixbuf.get_height()/2
		return [x, y]

	def create_selection_from_coord(self):
		x0 = self.past_x[0]
		x1 = self.past_x[1]
		y0 = self.past_y[0]
		y1 = self.past_y[1]
		if self.past_x[0] > self.past_x[1]:
			x0 = self.past_x[1]
			x1 = self.past_x[0]
		if self.past_y[0] > self.past_y[1]:
			y0 = self.past_y[1]
			y1 = self.past_y[0]
		self.window._pixbuf_manager.create_rectangle_selection_from_main(x0, y0, x1, y1)

	def draw_selection_area(self, show):
		self.row.set_active(True)
		self.window._pixbuf_manager.show_selection_rectangle()
		self.set_popover_position()
		self.show_popover(show)

	def set_popover_position(self):
		rectangle = Gdk.Rectangle()
		[rectangle.x, rectangle.y] = self.get_center_of_selection()
		rectangle.height = 1
		rectangle.width = 1
		self.selection_popover.set_pointing_to(rectangle)

	def drag_to(self, final_x, final_y):
		self.selection_has_been_used = True # XXX si delta non nuls seulement
		self.restore_pixbuf()
		delta_x = final_x - self.x_press
		delta_y = final_y - self.y_press
		self.past_x[0] += delta_x
		self.past_x[1] += delta_x
		self.past_y[0] += delta_y
		self.past_y[1] += delta_y
		self.window._pixbuf_manager.selection_x += delta_x
		self.window._pixbuf_manager.selection_y += delta_y
		self.window._pixbuf_manager.show_selection_rectangle()
		self.set_popover_position()
		self.non_destructive_show_modif()

	def action_import(self, *args):
		file_chooser = Gtk.FileChooserNative.new(_("Import a picture"), self.window,
			Gtk.FileChooserAction.OPEN,
			_("Import"),
			_("Cancel"))
		allPictures = Gtk.FileFilter()
		allPictures.set_name(_("All pictures"))
		allPictures.add_mime_type('image/png')
		allPictures.add_mime_type('image/jpeg')
		allPictures.add_mime_type('image/bmp')
		file_chooser.add_filter(allPictures)
		response = file_chooser.run()
		if response == Gtk.ResponseType.ACCEPT:
			fn = file_chooser.get_filename()
			self.window._pixbuf_manager.selection_pixbuf = GdkPixbuf.Pixbuf.new_from_file(fn)
			self.window._pixbuf_manager.create_selection_from_selection()
			self.draw_selection_area(False)
			self.selection_has_been_used = True
			self.non_destructive_show_modif()
		file_chooser.destroy()

	def action_cut(self, *args):
		self.selection_has_been_used = True
		self.window._pixbuf_manager.cut_operation()
		self.show_popover(False)
		self.apply_to_pixbuf()

	def action_copy(self, *args):
		self.selection_has_been_used = True
		self.window._pixbuf_manager.copy_operation()

	def action_paste(self, *args):
		self.selection_has_been_used = True
		self.window._pixbuf_manager.paste_operation()
		self.draw_selection_area(False)
		self.non_destructive_show_modif()

	def action_select_all(self, *args):
		self.selection_has_been_used = False
		self.window._pixbuf_manager.select_all()
		self.draw_selection_area(True)

	def action_unselect(self, *args):
		self.give_back_control()
		self.non_destructive_show_modif() # utile ??

	def action_selection_delete(self, *args):
		self.selection_has_been_used = True
		self.window._pixbuf_manager.delete_operation()
		self.apply_to_pixbuf()
		self.end_selection()
		self.window._pixbuf_manager.reset_selection()

	def action_selection_resize(self, *args):
		self.selection_has_been_used = True # FIXME ça devrait retourner un truc
		self.window.scale_pixbuf(True)

	def action_selection_crop(self, *args):
		crop_dialog = DrawingCropDialog(self.window, True, True)
		result = crop_dialog.run()
		if result == Gtk.ResponseType.APPLY:
			crop_dialog.on_apply()
			self.selection_has_been_used = True
		else:
			crop_dialog.on_cancel()

	def action_selection_rotate(self, *args): # TODO
		self.selection_has_been_used = True
		print("selection_rotate")

	def action_selection_export(self, *args):
		self.window._pixbuf_manager.export_selection_as()

	def draw_polygon(self, event):
		w_context = cairo.Context(self.window.get_surface())
		w_context.set_source_rgba(0.5, 0.5, 0.5, 0.5)
		w_context.set_dash([3, 3])

		if self.past_x[0] == -1:
			self.init_polygon(w_context)
		else:
			w_context.append_path(self._path)

		if self.past_x[0] != -1 and self.past_y[0] != -1 \
		and (max(event.x, self.past_x[0]) - min(event.x, self.past_x[0]) < self.closing_precision) \
		and (max(event.y, self.past_y[0]) - min(event.y, self.past_y[0]) < self.closing_precision):
			selection_path = self.finish_polygon(w_context)
			return True, selection_path
		else:
			self.continue_polygon(w_context, event.x, event.y)
			return False, None

	def init_polygon(self, w_context):
		(self.past_x[0], self.past_y[0]) = (self.x_press, self.y_press)
		w_context.move_to(self.x_press, self.y_press)
		self._path = w_context.copy_path()

	def continue_polygon(self, w_context, x, y):
		w_context.line_to(int(x), int(y))
		w_context.stroke_preserve() # draw the line without closing the path
		self._path = w_context.copy_path()
		self.non_destructive_show_modif()

	def finish_polygon(self, w_context):
		w_context.close_path()
		w_context.stroke_preserve()
		selection_path = w_context.copy_path()
		return selection_path

	def on_motion_on_area(self, area, event, surface):
		if not self.window._pixbuf_manager.selection_is_active:
			if self.selected_type_id == 'freehand':
				self.restore_pixbuf()
				self.draw_polygon(event)
