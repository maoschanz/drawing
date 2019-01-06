# select.py

from gi.repository import Gtk, Gdk, Gio, GdkPixbuf, GLib
import cairo

from .tools import ToolTemplate

class ToolSelect(ToolTemplate):
	__gtype_name__ = 'ToolSelect'

	closing_precision = 10

	def __init__(self, window, **kwargs):
		super().__init__('select', _("Selection"), 'edit-select-symbolic', window)

		self.selection_x = 1
		self.selection_y = 1
		self.selection_path = None
		self.temp_x = 1
		self.temp_y = 1
		self.selection_pixbuf = None
		self.temp_pixbuf = None

		#############################

		self.add_tool_action('selection_unselect', self.action_unselect) # pareil que give_back_control ?
		self.add_tool_action('selection_cut', self.action_cut)
		self.add_tool_action('selection_copy', self.action_copy)
		self.add_tool_action('selection_delete', self.action_selection_delete)
		self.add_tool_action('selection_crop', self.action_selection_crop)
		self.add_tool_action('selection_scale', self.action_selection_scale)
		self.add_tool_action('selection_rotate', self.action_selection_rotate)
		self.add_tool_action('selection_export', self.action_selection_export)
		self.add_tool_action('import', self.action_import)
		self.add_tool_action('paste', self.action_paste)
		self.add_tool_action('select_all', self.action_select_all)

		#############################

		self.selected_type_id = 'rectangle'
		self.selected_type_label = _("Rectangle")
		self.background_type_id = 'transparent'

		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/Drawing/tools/ui/select.ui')
		menu_r = builder.get_object('right-click-menu')
		self.rightc_popover = Gtk.Popover.new_from_model(self.window.drawing_area, menu_r)
		menu_l = builder.get_object('left-click-menu')
		self.selection_popover = Gtk.Popover.new_from_model(self.window.drawing_area, menu_l)
		self.selection_popover.set_relative_to(self.window.drawing_area)

		#############################

		self.add_tool_action_enum('selection_type', self.selected_type_id, self.on_change_active_type)
		self.add_tool_action_boolean('selection_exclude', False, self.osef)
		self.add_tool_action_enum('selection_background', self.background_type_id, self.osef)

		self.selected_type_id = 'rectangle'
		self.selected_type_label = _("Rectangle")

		#############################

		self.reset_selection()

	def on_tool_selected(self):
		self.selection_has_been_used = True
		self.update_actions_state()

	def on_tool_unselected(self):
		self.set_actions_state(False)

	def update_actions_state(self):
		self.set_actions_state(self.selection_is_active)

	def set_actions_state(self, state):
		self.set_action_sensitivity('selection_unselect', state)
		self.set_action_sensitivity('selection_cut', state)
		self.set_action_sensitivity('selection_copy', state)
		self.set_action_sensitivity('selection_delete', state)
		self.set_action_sensitivity('selection_crop', state)
		self.set_action_sensitivity('selection_scale', state)
		self.set_action_sensitivity('selection_rotate', state)
		self.set_action_sensitivity('selection_export', state)

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
			if self.selection_is_active:
				self.restore_pixbuf()
				self.delete_temp()
				self.window.show_pixbuf_content_at(self.selection_pixbuf, self.selection_x, self.selection_y)
				self.apply_to_pixbuf()
			self.reset_selection()
			return False
		else:
			self.selection_has_been_used = True
			return self.cancel_ongoing_operation()

	def cancel_ongoing_operation(self):
		print('cancel_ongoing_operation')
		self.reset_selection()
		self.restore_pixbuf()
		self.non_destructive_show_modif()
		return True

	def reset_selection(self):
		self.selection_is_active = False
		self.show_popover(False)
		self.x_press = 0.0
		self.y_press = 0.0
		self.past_x = [-1, -1]
		self.past_y = [-1, -1]
		self.selection_path = None
		self.selection_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 1, 1) # 8 ??? les autres plantent
		self.update_actions_state()

	def show_popover(self, state):
		self.selection_popover.popdown()
		self.rightc_popover.popdown()
		if self.selection_is_active and state:
			self.set_popover_position()
			self.selection_popover.popup()
		elif state:
			self.temp_x = self.rightc_popover.get_pointing_to()[1].x
			self.temp_y = self.rightc_popover.get_pointing_to()[1].y
			self.selection_x = self.rightc_popover.get_pointing_to()[1].x
			self.selection_y = self.rightc_popover.get_pointing_to()[1].y
			self.rightc_popover.popup()

	def on_motion_on_area(self, area, event, surface):
		if not self.selection_is_active:
			if self.selected_type_id == 'freehand':
				self.restore_pixbuf()
				self.draw_polygon(event)

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
			if not self.selection_is_active:
				self.past_x[0] = event.x
				self.past_x[1] = self.x_press
				self.past_y[0] = event.y
				self.past_y[1] = self.y_press
				self.create_selection_from_coord()
				if self.selection_is_active:
					self.force_and_draw_selection_area(True)
					self.selection_has_been_used = False
			elif self.point_is_in_selection(self.x_press, self.y_press):
				self.drag_to(event.x, event.y)
			else:
				self.give_back_control()
				return
		elif self.selected_type_id == 'freehand':
			if not self.selection_is_active:
				if self.draw_polygon(event):
					self.restore_pixbuf()
					self.create_free_selection_from_main()
					if self.selection_is_active:
						self.force_and_draw_selection_area(True)
						self.selection_has_been_used = False
					(self.x_press, self.y_press) = (-1.0, -1.0)
					self.past_x = [-1, -1]
					self.past_y = [-1, -1]
			elif self.point_is_in_selection(self.x_press, self.y_press):
				self.drag_to(event.x, event.y)
			else:
				self.give_back_control()

	def get_center_of_selection(self):
		x = self.selection_x + self.selection_pixbuf.get_width()/2
		y = self.selection_y + self.selection_pixbuf.get_height()/2
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
		self.create_rectangle_selection_from_main(x0, y0, x1, y1)

	def force_and_draw_selection_area(self, show_menu):
		self.row.set_active(True)
		self.show_selection_overlay()
		self.show_popover(show_menu)

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
		self.selection_x += delta_x
		self.selection_y += delta_y
		self.show_selection_overlay()
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
			self.selection_pixbuf = GdkPixbuf.Pixbuf.new_from_file(fn)
			self.create_selection_from_arbitrary_pixbuf()
		file_chooser.destroy()

	def action_cut(self, *args):
		self.selection_has_been_used = True
		self.copy_operation()
		self.delete_temp()
		self.reset_selection()
		self.apply_to_pixbuf()

	def action_copy(self, *args):
		self.selection_has_been_used = True
		self.copy_operation()

	def copy_operation(self):
		cb = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
		cb.set_image(self.selection_pixbuf)

	def action_paste(self, *args):
		cb = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
		self.selection_pixbuf = cb.wait_for_image()
		self.create_selection_from_arbitrary_pixbuf()

	def action_select_all(self, *args):
		self.selection_has_been_used = False
		self.temp_x = 0
		self.temp_y = 0
		self.selection_x = 0
		self.selection_y = 0
		self.selection_pixbuf = self.window.main_pixbuf.copy()
		w_context = cairo.Context(self.window.get_surface())
		w_context.move_to(0, 0)
		w_context.line_to(self.window.get_pixbuf_width(), 0)
		w_context.line_to(self.window.get_pixbuf_width(), self.window.get_pixbuf_height())
		w_context.line_to(0, self.window.get_pixbuf_height())
		w_context.close_path()
		self.selection_path = w_context.copy_path()
		self.set_temp()
		self.force_and_draw_selection_area(True)

	def action_unselect(self, *args):
		self.give_back_control()
		self.non_destructive_show_modif() # utile ??

	def action_selection_delete(self, *args):
		self.selection_has_been_used = True
		self.restore_pixbuf()
		self.delete_temp()
		self.reset_selection()
		self.apply_to_pixbuf()

	def action_selection_scale(self, *args):
		self.selection_has_been_used = True # XXX pas forcément !!
		self.window.active_mode().on_cancel_mode()
		self.window.scale_mode.on_mode_selected(True)
		self.window.update_bottom_panel('scale')

	def action_selection_crop(self, *args):
		self.selection_has_been_used = True # XXX pas forcément !!
		self.window.active_mode().on_cancel_mode()
		self.window.crop_mode.on_mode_selected(True, True)
		self.window.update_bottom_panel('crop')

	def action_selection_rotate(self, *args): # TODO
		self.selection_has_been_used = True # XXX pas forcément !!
		self.window.active_mode().on_cancel_mode()
		self.window.rotate_mode.on_mode_selected(True)
		self.window.update_bottom_panel('rotate')

	def action_selection_export(self, *args):
		file_path = self.window.run_save_file_chooser('')
		if file_path is not None:
			self.selection_pixbuf.savev(file_path, file_path.split('.')[-1], [None], [])

##############################

	def draw_polygon(self, event):
		w_context = cairo.Context(self.window.get_surface())
		w_context.set_source_rgba(0.5, 0.5, 0.5, 0.5)
		w_context.set_dash([3, 3])

		if self.selection_path is None:
			(self.past_x[0], self.past_y[0]) = (self.x_press, self.y_press)
			w_context.move_to(self.x_press, self.y_press)
			self.selection_path = w_context.copy_path()
		elif (max(event.x, self.past_x[0]) - min(event.x, self.past_x[0]) < self.closing_precision) \
		and (max(event.y, self.past_y[0]) - min(event.y, self.past_y[0]) < self.closing_precision):
			w_context.append_path(self.selection_path)
			w_context.close_path()
			w_context.stroke_preserve()
			self.selection_path = w_context.copy_path()
			return True
		else:
			w_context.append_path(self.selection_path)
			self.continue_polygon(w_context, event.x, event.y)
			return False

	def continue_polygon(self, w_context, x, y):
		w_context.line_to(int(x), int(y))
		w_context.stroke_preserve() # draw the line without closing the path
		self.selection_path = w_context.copy_path()
		self.non_destructive_show_modif()

####################################

	def create_selection_from_arbitrary_pixbuf(self):
		self.selection_has_been_used = True
		self.selection_is_active = True
		w_context = cairo.Context(self.window.get_surface())
		w_context.move_to(self.selection_x, self.selection_y)
		w_context.rel_line_to(self.selection_pixbuf.get_width(), 0)
		w_context.rel_line_to(0, self.selection_pixbuf.get_height())
		w_context.rel_line_to(-1 * self.selection_pixbuf.get_width(), 0)
		w_context.close_path()
		self.selection_path = w_context.copy_path()
		self.force_and_draw_selection_area(False)
		self.temp_pixbuf = None
		self.update_actions_state()
		self.non_destructive_show_modif()

	def set_temp(self):
		self.temp_x = self.selection_x
		self.temp_y = self.selection_y
		self.temp_pixbuf = self.selection_pixbuf.copy()
		self.selection_is_active = True
		self.update_actions_state()

	def delete_temp(self):
		if self.temp_pixbuf is None:
			return
		w_context = cairo.Context(self.window.get_surface())
		w_context.new_path()
		w_context.append_path(self.selection_path)
		w_context.clip()
		w_context.set_operator(cairo.Operator.CLEAR)
		w_context.paint()
		w_context.set_operator(cairo.Operator.OVER)

	def point_is_in_selection(self, x, y):
		dragged_path = self.get_dragged_selection_path()
		w_context = cairo.Context(self.window.get_surface())
		w_context.new_path()
		w_context.append_path(dragged_path)
		return w_context.in_fill(x, y)

	def show_selection_overlay(self):
		self.restore_pixbuf()
		if self.selection_is_active:
			self.delete_temp()
		self.window.show_pixbuf_content_at(self.selection_pixbuf, self.selection_x, self.selection_y)
		w_context = cairo.Context(self.window.get_surface())
		w_context.new_path()
		w_context.set_dash([3, 3])
		dragged_path = self.get_dragged_selection_path()
		w_context.append_path(dragged_path)
		w_context.clip_preserve()
		w_context.set_source_rgba(0.1, 0.1, 0.3, 0.2)
		w_context.paint()
		w_context.set_source_rgba(0.5, 0.5, 0.5, 0.5)
		w_context.stroke()
		self.window.drawing_area.queue_draw()

	def get_dragged_selection_path(self):
		w_context = cairo.Context(self.window.get_surface())
		for pts in self.selection_path:
			if pts[1] is not ():
				x = pts[1][0] + self.selection_x - self.temp_x
				y = pts[1][1] + self.selection_y - self.temp_y
				w_context.line_to(int(x), int(y))
		w_context.close_path()
		return w_context.copy_path()

	def scale_pixbuf_to(self, new_width, new_height): # N'est utilisée qu'une seule fois, dans scale.py
		self.selection_pixbuf = self.selection_pixbuf.scale_simple(new_width, new_height, GdkPixbuf.InterpType.TILES)
		self.show_selection_overlay()

	def create_free_selection_from_main(self):
		self.selection_pixbuf = self.window.main_pixbuf.copy()
		surface = Gdk.cairo_surface_create_from_pixbuf(self.selection_pixbuf, 0, None)
		xmin, ymin = surface.get_width(), surface.get_height()
		xmax, ymax = 0.0, 0.0
		for pts in self.selection_path:
			if pts[1] is not ():
				xmin = min(pts[1][0], xmin)
				xmax = max(pts[1][0], xmax)
				ymin = min(pts[1][1], ymin)
				ymax = max(pts[1][1], ymax)
		xmax = min(xmax, surface.get_width())
		ymax = min(ymax, surface.get_height())
		xmin = max(xmin, 0.0)
		ymin = max(ymin, 0.0)
		self.crop_selection_surface(xmin, ymin, xmax - xmin, ymax - ymin)
		self.selection_x = xmin
		self.selection_y = ymin
		w_context = cairo.Context(surface)
		w_context.set_operator(cairo.Operator.DEST_IN)
		w_context.new_path()
		w_context.append_path(self.selection_path)
		w_context.fill()
		w_context.set_operator(cairo.Operator.OVER)
		self.selection_pixbuf = Gdk.pixbuf_get_from_surface(surface, xmin, ymin, \
			xmax - xmin, ymax - ymin)
		self.set_temp()

	def create_rectangle_selection_from_main(self, x0, y0, x1, y1):
		x0 = int(x0)
		x1 = int(x1)
		y0 = int(y0)
		y1 = int(y1)
		w = x1 - x0
		h = y1 - y0
		if w <= 0 or h <= 0:
			return
		self.selection_x = x0
		self.selection_y = y0
		temp_surface = Gdk.cairo_surface_create_from_pixbuf(self.window.main_pixbuf, 0, None)
		temp_surface = temp_surface.map_to_image(cairo.RectangleInt(x0, y0, w, h))
		self.selection_pixbuf = Gdk.pixbuf_get_from_surface(temp_surface, 0, 0, \
			temp_surface.get_width(), temp_surface.get_height())
		w_context = cairo.Context(self.window.get_surface())
		w_context.move_to(x0, y0)
		w_context.line_to(x1, y0)
		w_context.line_to(x1, y1)
		w_context.line_to(x0, y1)
		w_context.close_path()
		self.selection_path = w_context.copy_path()
		self.set_temp()

	def crop_selection_surface(self, x, y, width, height):
		x = int(x)
		y = int(y)
		width = int(width)
		height = int(height)
		if self.selection_pixbuf is None:
			return
		selection_surface = Gdk.cairo_surface_create_from_pixbuf(self.selection_pixbuf, 0, None)

		# The cairo.Surface.map_to_image method works only when reducing the size,
		# but the selection can not grow form this method.
		selection_surface = Gdk.cairo_surface_create_from_pixbuf(self.selection_pixbuf, 0, None)
		selection_surface = selection_surface.map_to_image(cairo.RectangleInt(x, y, width, height))
		self.selection_pixbuf = Gdk.pixbuf_get_from_surface(selection_surface, 0, 0, \
			selection_surface.get_width(), selection_surface.get_height())
