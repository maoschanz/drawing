# image.py
#
# Copyright 2019 Romain F. T.
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

from gi.repository import Gtk, Gdk, Gio, GdkPixbuf, GLib, Pango
import cairo

from .gi_composites import GtkTemplate

from .utilities import utilities_save_pixbuf_at
from .utilities import utilities_show_overlay_on_context

@GtkTemplate(ui='/com/github/maoschanz/drawing/ui/image.ui')
class DrawingImage(Gtk.Box):
	__gtype_name__ = 'DrawingImage'

	drawing_area = GtkTemplate.Child()
	h_scrollbar = GtkTemplate.Child()
	v_scrollbar = GtkTemplate.Child()

	closing_precision = 10

	def __init__(self, window, **kwargs):
		super().__init__(**kwargs)
		self.window = window
		self.init_template()

		self.gfile = None
		self.filename = None
		self.is_clicked = False
		self.build_tab_label()

		self.drawing_area.add_events( \
			Gdk.EventMask.BUTTON_PRESS_MASK | \
			Gdk.EventMask.BUTTON_RELEASE_MASK | \
			Gdk.EventMask.POINTER_MOTION_MASK | \
			Gdk.EventMask.SMOOTH_SCROLL_MASK | \
			Gdk.EventMask.ENTER_NOTIFY_MASK | \
			Gdk.EventMask.LEAVE_NOTIFY_MASK)
		# Utiliser BUTTON_MOTION_MASK au lieu de POINTER_MOTION_MASK serait plus
		# efficace mais moins puissant

		# For displaying things on the widget
		self.drawing_area.connect('draw', self.on_draw)
		# For drawing with tools
		self.drawing_area.connect('motion-notify-event', self.on_motion_on_area)
		self.drawing_area.connect('button-press-event', self.on_press_on_area)
		self.drawing_area.connect('button-release-event', self.on_release_on_area)
		# For scrolling
		self.drawing_area.connect('scroll-event', self.on_scroll_on_area)
		self.h_scrollbar.connect('value-changed', self.on_scrollbar_value_change)
		self.v_scrollbar.connect('value-changed', self.on_scrollbar_value_change)
		# For the cursor
		self.drawing_area.connect('enter-notify-event', self.on_enter_image)
		self.drawing_area.connect('leave-notify-event', self.on_leave_image)

	def init_image(self):
		"""Part of the initialization common to both a new blank image and an
		opened image."""
		self.undo_history = []
		self.redo_history = []
		self._is_saved = True
		self.zoom_level = 1.0
		self.scroll_x = 0
		self.scroll_y = 0
		self.selection_x = 1
		self.selection_y = 1
		self.selection_path = None
		self.selection_is_active = False # XXX ?
		self.selection_has_been_used = False # TODO
		self.closing_x = 0
		self.closing_y = 0
		self.reset_temp()
		self.window.lookup_action('undo').set_enabled(False)
		self.window.lookup_action('redo').set_enabled(False)

	def build_tab_label(self):
		"""Build the "self.tab_title" attribute, which is the GTK widget
		displayed as the tab title."""
		self.tab_title = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, expand=True)
		self.tab_label = Gtk.Label(label=self.get_filename_for_display())
		self.tab_label.set_ellipsize(Pango.EllipsizeMode.END)
		btn = Gtk.Button.new_from_icon_name('window-close-symbolic', Gtk.IconSize.BUTTON)
		btn.set_relief(Gtk.ReliefStyle.NONE)
		btn.connect('clicked', self.try_close_tab)
		if self.window.decorations == 'csd-eos':
			self.tab_title.pack_start(btn, expand=False, fill=False, padding=0)
			self.tab_title.pack_end(self.tab_label, expand=True, fill=True, padding=0)
		else:
			self.tab_title.pack_start(self.tab_label, expand=True, fill=True, padding=0)
			self.tab_title.pack_end(btn, expand=False, fill=False, padding=0)
		self.tab_title.show_all()

	def update_title(self):
		main_title = self.get_filename_for_display()
		if not self._is_saved:
			main_title = '*' + main_title
		self.set_tab_label(main_title)
		return main_title

	def get_filename_for_display(self):
		if self.get_file_path() is None:
			unsaved_file_name = _("Unsaved file")
		else:
			unsaved_file_name = self.get_file_path().split('/')[-1]
		return unsaved_file_name

	def try_close_tab(self, *args):
		"""Ask the window to close the image/tab. Then unallocate widgets and
		pixbufs."""
		if self.window.close_tab(self):
			self.destroy()
			self.main_pixbuf = None
			self.selection_pixbuf = None
			self.temp_pixbuf = None
			return True
		else:
			return False

	def init_background(self, *args):
		width = self.window._settings.get_int('default-width')
		height = self.window._settings.get_int('default-height')
		background_rgba = self.window._settings.get_strv('background-rgba')
		r = float(background_rgba[0])
		g = float(background_rgba[1])
		b = float(background_rgba[2])
		a = float(background_rgba[3])
		self.initial_operation = {
			'tool_id': None,
			'pixbuf': None,
			'red': r,
			'green': g,
			'blue': b,
			'alpha': a,
			'width': width,
			'height': height
		}
		self.restore_first_pixbuf()
		self.init_image()

	def try_load_pixbuf(self, pixbuf):
		if not pixbuf.get_has_alpha() and self.window._settings.get_boolean('add-alpha'):
			pixbuf = pixbuf.add_alpha(False, 0, 0, 0)
		self.initial_operation = {
			'tool_id': None,
			'pixbuf': pixbuf,
			'red': 0.0,
			'green': 0.0,
			'blue': 0.0,
			'alpha': 0.0,
			'width': pixbuf.get_width(),
			'height': pixbuf.get_height()
		}
		self.main_pixbuf = pixbuf
		self.restore_first_pixbuf()
		self.init_image()
		self.update_title()

	def restore_first_pixbuf(self):
		"""Set the first saved pixbuf as the main_pixbuf. This is used to
		rebuild the picture from its history."""
		pixbuf = self.initial_operation['pixbuf']
		width = self.initial_operation['width']
		height = self.initial_operation['height']
		self.temp_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 1, 1)
		self.selection_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 1, 1)
		self.surface = cairo.ImageSurface(cairo.Format.ARGB32, width, height)
		if pixbuf is None:
			r = self.initial_operation['red']
			g = self.initial_operation['green']
			b = self.initial_operation['blue']
			a = self.initial_operation['alpha']
			self.main_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, \
			                                             True, 8, width, height)
			cairo_context = cairo.Context(self.surface)
			cairo_context.set_source_rgba(r, g, b, a)
			cairo_context.paint()
			self.update()
			self.set_surface_as_stable_pixbuf()
		else:
			self.main_pixbuf = self.initial_operation['pixbuf'].copy()
			self.use_stable_pixbuf()

	def on_enter_image(self, *args):
		self.window.set_cursor(True)

	def on_leave_image(self, *args):
		self.window.set_cursor(False)

	# FILE MANAGEMENT

	def get_file_path(self):
		if self.gfile is None:
			return None
		else:
			return self.gfile.get_path()

	def try_load_file(self, gfile):
		self.gfile = gfile
		self.main_pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.get_file_path())
		pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.get_file_path())
		if not pixbuf.get_has_alpha() and self.window._settings.get_boolean('add-alpha'):
			pixbuf = pixbuf.add_alpha(False, 0, 0, 0)
		self.initial_operation = {
			'tool_id': None,
			'pixbuf': pixbuf,
			'red': 0.0,
			'green': 0.0,
			'blue': 0.0,
			'alpha': 0.0,
			'width': pixbuf.get_width(),
			'height': pixbuf.get_height()
		}
		self.restore_first_pixbuf()
		self.init_image()
		self.update_title()

	def set_tab_label(self, title):
		self.tab_label.set_label(title)

	def post_save(self):
		self._is_saved = True
		self.use_stable_pixbuf()
		self.update()

	# HISTORY MANAGEMENT

	def try_undo(self, *args):
		self.active_tool().cancel_ongoing_operation()
		if len(self.undo_history) != 0:
			self.redo_history.append(self.undo_history.pop())
		# TODO implement operation_is_ongoing
		# if self.window.operation_is_ongoing():
		# 	self.active_tool().cancel_ongoing_operation()
		# elif len(self.undo_history) != 0:
		# 	self.redo_history.append(self.undo_history.pop())

	def try_redo(self, *args):
		self.undo_history.append(self.redo_history.pop())

	def update_history_sensitivity(self):
		can_undo = ( len(self.undo_history) != 0 ) or self.window.operation_is_ongoing()
		self.window.lookup_action('undo').set_enabled(can_undo)
		self.window.lookup_action('redo').set_enabled(len(self.redo_history) != 0)
		# self.update_history_actions_labels() # TODO

	def update_history_actions_labels(self):
		undo_label = self.undo_history[-1:]
		redo_label = self.redo_history[-1:]
		if len(undo_label) > 0:
			undo_label = undo_label[0]['tool_id'] # TODO store a translatable label
		else:
			undo_label = None
		if len(redo_label) > 0:
			redo_label = redo_label[0]['tool_id'] # TODO store a translatable label
		else:
			redo_label = None
		self.window.update_history_actions_labels(undo_label, redo_label)

	def add_operation_to_history(self, operation):
		self._is_saved = False
		self.undo_history.append(operation)
		self.update_history_sensitivity()

	def on_tool_finished(self):
		#self.redo_history = []
		self.update_history_sensitivity()
		self.update()
		self.set_surface_as_stable_pixbuf()
		self.update_actions_state()

	def set_action_sensitivity(self, action_name, state):
		self.window.lookup_action(action_name).set_enabled(state)

	def update_actions_state(self):
		state = self.selection_is_active
		self.set_action_sensitivity('unselect', state)
		self.set_action_sensitivity('selection_cut', state)
		self.set_action_sensitivity('selection_copy', state)
		self.set_action_sensitivity('selection_delete', state)
		self.set_action_sensitivity('selection_export', state)
		self.set_action_sensitivity('new_tab_selection', state)
		self.active_tool().update_actions_state()

	# DRAWING OPERATIONS

	def on_draw(self, area, cairo_context):
		"""Signal callback. Executed when self.drawing_area is redrawn."""
		cairo_context.scale(self.zoom_level, self.zoom_level)
		cairo_context.set_source_surface(self.get_surface(), \
		                                 -1 * self.scroll_x, -1 * self.scroll_y)
		cairo_context.paint()

		if self.is_using_selection() and self.selection_pixbuf is not None:
			utilities_show_overlay_on_context(cairo_context, \
			                            self.get_dragged_selection_path(), True)

	def on_press_on_area(self, area, event):
		"""Signal callback. Executed when a mouse button is pressed on
		self.drawing_area, if the button is the mouse wheel the colors are
		exchanged, otherwise the signal is transmitted to the selected tool."""
		if event.button == 2:
			self.is_clicked = False
			self.window.action_exchange_color()
			return
		self.is_clicked = True
		event_x = (self.scroll_x + event.x) / self.zoom_level
		event_y = (self.scroll_y + event.y) / self.zoom_level
		self.active_tool().on_press_on_area(area, event, self.surface, \
		                            self.window.thickness_spinbtn.get_value(), \
		          self.get_left_rgba(), self.get_right_rgba(), event_x, event_y)

	def on_motion_on_area(self, area, event):
		"""Signal callback. Executed when the mouse pointer moves upon
		self.drawing_area, the signal is transmitted to the selected tool.
		If a button (not the mouse wheel) is pressed, the tool's method should
		have an effect on the image, otherwise it shouldn't change anything
		except the mouse cursor icon for example."""
		if not self.is_clicked:
			self.active_tool().on_unclicked_motion_on_area(event, self.surface)
			return
		event_x = (self.scroll_x + event.x) / self.zoom_level
		event_y = (self.scroll_y + event.y) / self.zoom_level
		self.active_tool().on_motion_on_area(area, event, self.surface, event_x, event_y)
		self.update()

	def on_release_on_area(self, area, event):
		"""Signal callback. Executed when a mouse button is released on
		self.drawing_area, if the button is not the signal is transmitted to the
		selected tool."""
		if not self.is_clicked:
			return
		self.is_clicked = False
		event_x = (self.scroll_x + event.x) / self.zoom_level
		event_y = (self.scroll_y + event.y) / self.zoom_level
		self.active_tool().on_release_on_area(area, event, self.surface, event_x, event_y)
		self.window.set_picture_title()

	def active_tool(self):
		return self.window.active_tool()

	def get_right_rgba(self):
		return self.window.color_popover_r.color_widget.get_rgba()

	def get_left_rgba(self):
		return self.window.color_popover_l.color_widget.get_rgba()

	def on_scroll_on_area(self, area, event):
		self.add_deltas(event.delta_x, event.delta_y, 10)

	def on_scrollbar_value_change(self, scrollbar):
		self.correct_coords(self.h_scrollbar.get_value(), self.v_scrollbar.get_value())
		self.update()

	def add_deltas(self, delta_x, delta_y, factor):
		incorrect_x = self.scroll_x + int(delta_x * factor)
		incorrect_y = self.scroll_y + int(delta_y * factor)
		self.correct_coords(incorrect_x, incorrect_y)
		self.window.minimap.update_minimap()

	def correct_coords(self, incorrect_x, incorrect_y): # FIXME doesn't work with the zoom
		# Forbid absurd values
		if self.drawing_area.get_allocated_width() < 2:
			return
		mpb_width = self.get_main_pixbuf().get_width()
		mpb_height = self.get_main_pixbuf().get_height()
		if incorrect_x + self.drawing_area.get_allocated_width() > mpb_width:
			incorrect_x = mpb_width - self.drawing_area.get_allocated_width()
		if incorrect_y + self.drawing_area.get_allocated_height() > mpb_height:
			incorrect_y = mpb_height - self.drawing_area.get_allocated_height()
		if incorrect_x < 0:
			incorrect_x = 0
		if incorrect_y < 0:
			incorrect_y = 0

		# Update the horizontal scrollbar
		self.h_scrollbar.set_visible(self.drawing_area.get_allocated_width() < mpb_width)
		self.h_scrollbar.set_range(0, mpb_width)
		self.h_scrollbar.get_adjustment().set_page_size( \
		                                self.drawing_area.get_allocated_width())
		self.h_scrollbar.set_value(incorrect_x)
		self.scroll_x = self.h_scrollbar.get_value()

		# Update the vertical scrollbar
		self.v_scrollbar.set_visible(self.drawing_area.get_allocated_height() < mpb_height)
		self.v_scrollbar.set_range(0, mpb_height)
		self.v_scrollbar.get_adjustment().set_page_size( \
		                               self.drawing_area.get_allocated_height())
		self.v_scrollbar.set_value(incorrect_y)
		self.scroll_y = self.v_scrollbar.get_value()

	def inc_zoom_level(self, delta):
		self.set_zoom_level((self.zoom_level * 100) + delta)

	def set_zoom_level(self, level):
		self.zoom_level = (level/100)
		self.window.minimap.update_zoom_scale(self.zoom_level)
		self.update()

	def set_opti_zoom_level(self):
		h_ratio = self.drawing_area.get_allocated_width() / self.main_pixbuf.get_width()
		v_ratio = self.drawing_area.get_allocated_height() / self.main_pixbuf.get_height()
		opti = min(h_ratio, v_ratio) * 99 # Not 100 because some little margin is cool
		self.set_zoom_level(opti)

#######################

	def get_main_pixbuf(self):
		return self.main_pixbuf

	def get_pixbuf_width(self):
		return self.main_pixbuf.get_width()

	def get_pixbuf_height(self):
		return self.main_pixbuf.get_height()

	def set_main_pixbuf(self, new_pixbuf):
		if new_pixbuf is None:
			return False
		else:
			self.main_pixbuf = new_pixbuf
			return True

########################

	def get_temp_pixbuf(self):
		return self.temp_pixbuf

	def set_temp_pixbuf(self, new_pixbuf):
		if new_pixbuf is None:
			return False
		else:
			self.temp_pixbuf = new_pixbuf
			return True

########################

	def on_import_selection(self):
		self.temp_path = None
		self.create_selection_from_arbitrary_pixbuf(False)

	def image_unselect(self, *args):
		self.window.get_selection_tool().give_back_control(False) # FIXME ?

	def image_delete(self, *args):
		self.selection_has_been_used = True
		self.use_stable_pixbuf()
		self.window.get_selection_tool().delete_selection()
		self.reset_temp()
		self.show_selection_popover(False)

########################

	def show_selection_popover(self, state):
		self.window.get_selection_tool().show_popover(state)

	def point_is_in_selection(self, tested_x, tested_y):
		"""Returns a boolean if the point whose coordinates are "(tested_x,
		tested_y)" is in the path defining the selection. If such path doesn't
		exist, it returns None."""
		if not self.selection_is_active:
			return True
		if self.selection_path is None:
			return None
		cairo_context = cairo.Context(self.get_surface())
		for pts in self.selection_path:
			if pts[1] is not ():
				x = pts[1][0] + self.selection_x - self.temp_x
				y = pts[1][1] + self.selection_y - self.temp_y
				cairo_context.line_to(int(x), int(y))
		return cairo_context.in_fill(tested_x, tested_y)

	def create_selection_from_arbitrary_pixbuf(self, is_existing_content):
		"""This method creates a rectangle selection from the currently set
		selection pixbuf.
		It can be the result of an editing operation (crop, scale, etc.), or it
		can be an imported picture (from a file or from the clipboard).
		In the first case, the "is_existing_content" boolean parameter should be
		true, so the temp_path will be cleared."""
		if self.selection_pixbuf is None:
			return
		self.temp_x = self.selection_x
		self.temp_y = self.selection_y
		self.selection_has_been_used = True
		self.selection_is_active = True
		cairo_context = cairo.Context(self.get_surface())
		cairo_context.move_to(self.selection_x, self.selection_y)
		cairo_context.rel_line_to(self.selection_pixbuf.get_width(), 0)
		cairo_context.rel_line_to(0, self.selection_pixbuf.get_height())
		cairo_context.rel_line_to(-1 * self.selection_pixbuf.get_width(), 0)
		cairo_context.close_path()
		self.selection_path = cairo_context.copy_path()
		if is_existing_content:
			self.temp_path = cairo_context.copy_path()
			self.set_temp()
		self.show_selection_popover(False)
		self.update_actions_state()
		self.window.get_selection_tool().update_surface()

	def create_free_selection_from_main(self):
		"""This method defines a selection pixbuf by copying the main pixbuf and
		deleting everything outside of the `selection_path`."""
		self.selection_pixbuf = self.get_main_pixbuf().copy()
		surface = Gdk.cairo_surface_create_from_pixbuf(self.selection_pixbuf, 0, None)
		xmin, ymin = surface.get_width(), surface.get_height()
		xmax, ymax = 0.0, 0.0
		if self.selection_path is None:
			return
		for pts in self.selection_path: # XXX cairo has a method for this
			if pts[1] is not ():
				xmin = min(pts[1][0], xmin)
				xmax = max(pts[1][0], xmax)
				ymin = min(pts[1][1], ymin)
				ymax = max(pts[1][1], ymax)
		xmax = min(xmax, surface.get_width())
		ymax = min(ymax, surface.get_height())
		xmin = max(xmin, 0.0)
		ymin = max(ymin, 0.0)
		if xmax - xmin < self.closing_precision and ymax - ymin < self.closing_precision:
			return # when the path is not drawable yet XXX
		self.crop_free_selection_pixbuf(xmin, ymin, xmax - xmin, ymax - ymin)
		cairo_context = cairo.Context(surface)
		cairo_context.set_operator(cairo.Operator.DEST_IN)
		cairo_context.new_path()
		cairo_context.append_path(self.selection_path)
		if self.temp_path is None: # ??
			self.temp_path = cairo_context.copy_path()
		cairo_context.fill()
		cairo_context.set_operator(cairo.Operator.OVER)
		self.selection_pixbuf = Gdk.pixbuf_get_from_surface(surface, \
		                                   xmin, ymin, xmax - xmin, ymax - ymin)
		self.set_temp()

	def draw_rectangle(self, event_x, event_y):
		"""Define the selection pixbuf and draw an overlay for a rectangle
		selection beginning where the "press" event was made and ending where
		the "release" event is made (its coordinates are parameters). This
		method is specific to the "rectangle selection" mode."""
		if self.selection_path is None:
			return
		cairo_context = cairo.Context(self.get_surface())
		cairo_context.set_source_rgba(0.5, 0.5, 0.5, 0.5)
		cairo_context.set_dash([3, 3])
		cairo_context.append_path(self.selection_path)
		press_x, press_y = cairo_context.get_current_point()

		x0 = int( min(press_x, event_x) )
		y0 = int( min(press_y, event_y) )
		x1 = int( max(press_x, event_x) )
		y1 = int( max(press_y, event_y) )
		w = x1 - x0
		h = y1 - y0
		if w <= 0 or h <= 0:
			self.selection_path = None
			return

		self.selection_x = x0
		self.selection_y = y0
		temp_surface = Gdk.cairo_surface_create_from_pixbuf(self.get_main_pixbuf(), 0, None)
		temp_surface = temp_surface.map_to_image(cairo.RectangleInt(x0, y0, w, h))
		self.set_selection_pixbuf( Gdk.pixbuf_get_from_surface(temp_surface, \
			0, 0, temp_surface.get_width(), temp_surface.get_height()) )

		cairo_context.new_path()
		cairo_context.move_to(x0, y0)
		cairo_context.line_to(x1, y0)
		cairo_context.line_to(x1, y1)
		cairo_context.line_to(x0, y1)
		cairo_context.close_path()

		self.selection_path = cairo_context.copy_path()
		self.temp_path = cairo_context.copy_path()
		self.set_temp()

	def init_path(self, event_x, event_y):
		"""This method moves the current path to the "press" event coordinates.
		It's used by both the 'rectangle selection' mode and the 'free
		selection' mode."""
		if self.selection_path is not None:
			return
		self.closing_x = event_x
		self.closing_y = event_y
		cairo_context = cairo.Context(self.get_surface())
		cairo_context.move_to(event_x, event_y)
		self.selection_path = cairo_context.copy_path()

	def draw_polygon(self, event_x, event_y):
		"""This method is specific to the 'free selection' mode."""
		cairo_context = cairo.Context(self.get_surface())
		cairo_context.set_source_rgba(0.5, 0.5, 0.5, 0.5)
		cairo_context.set_dash([3, 3])
		if self.selection_path is None:
			return False
		if (max(event_x, self.closing_x) - min(event_x, self.closing_x) < self.closing_precision) \
		and (max(event_y, self.closing_y) - min(event_y, self.closing_y) < self.closing_precision):
			cairo_context.append_path(self.selection_path)
			cairo_context.close_path()
			cairo_context.stroke_preserve()
			self.selection_path = cairo_context.copy_path()
			self.temp_path = cairo_context.copy_path()
			return True
		else:
			cairo_context.append_path(self.selection_path)
			cairo_context.line_to(int(event_x), int(event_y))
			cairo_context.stroke_preserve() # draw the line without closing the path
			self.selection_path = cairo_context.copy_path()
			self.update()
			return False

	def crop_free_selection_pixbuf(self, x, y, width, height):
		"""Reduce the size of the pixbuf generated by "create_free_selection_from_main"
		for usability and performance improvements.
		Before this method, the "selection_pixbuf" is a copy of the main one, but
		is mainly full of alpha, while "selection_x" and "selection_y" are zeros.
		After this method, the "selection_pixbuf" is smaller and coordinates make
		more sense."""
		x = int(x)
		y = int(y)
		width = int(width)
		height = int(height)
		min_w = min(width, self.selection_pixbuf.get_width() + x)
		min_h = min(height, self.selection_pixbuf.get_height() + y)
		new_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, width, height)
		new_pixbuf.fill(0)
		self.selection_pixbuf.copy_area(x, y, min_w, min_h, new_pixbuf, 0, 0)
		self.selection_pixbuf = new_pixbuf
		self.selection_x = x
		self.selection_y = y

	def reset_temp(self):
		self.selection_pixbuf = None
		self.selection_path = None
		self.temp_x = 0
		self.temp_y = 0
		self.temp_path = None
		self.selection_is_active = False
		# self.update_actions_state() # FIXME ne peut pas être ici car empêche le démarrage
		self.use_stable_pixbuf()
		self.update()

	def set_temp(self):
		self.temp_x = self.selection_x
		self.temp_y = self.selection_y
		self.selection_is_active = True
		self.update_actions_state()

	def delete_temp(self):
		if self.temp_path is None or not self.selection_is_active:
			return
		cairo_context = cairo.Context(self.get_surface())
		cairo_context.new_path()
		cairo_context.append_path(self.temp_path)
		cairo_context.clip()
		cairo_context.set_operator(cairo.Operator.CLEAR)
		cairo_context.paint()
		cairo_context.set_operator(cairo.Operator.OVER)

	def get_dragged_selection_path(self):
		if self.selection_path is None:
			return None
		cairo_context = cairo.Context(self.get_surface())
		for pts in self.selection_path:
			if pts[1] is not ():
				x = pts[1][0] + self.selection_x - self.temp_x - self.scroll_x
				y = pts[1][1] + self.selection_y - self.temp_y - self.scroll_y
				cairo_context.line_to(int(x), int(y))
		cairo_context.close_path()
		return cairo_context.copy_path()

	def get_selection_pixbuf(self):
		return self.selection_pixbuf

	def set_selection_pixbuf(self, new_pixbuf):
		if new_pixbuf is None:
			return False
		else:
			self.selection_pixbuf = new_pixbuf
			return True

	def image_select_all(self):
		self.selection_x = 0
		self.selection_y = 0
		self.set_selection_pixbuf(self.get_main_pixbuf().copy())
		self.selection_has_been_used = False # TODO non
		self.temp_x = 0
		self.temp_y = 0
		self.create_selection_from_arbitrary_pixbuf(True)
		self.show_selection_popover(True)

########################

	def update(self):
		self.drawing_area.queue_draw()

	def get_surface(self):
		return self.surface

	def set_surface_as_stable_pixbuf(self):
		self.main_pixbuf = Gdk.pixbuf_get_from_surface(self.surface, 0, 0, \
			self.surface.get_width(), self.surface.get_height())

	def use_stable_pixbuf(self):
		self.surface = Gdk.cairo_surface_create_from_pixbuf(self.main_pixbuf, 0, None)

	def is_using_selection(self):
		return self.window.tool_needs_selection() and self.selection_is_active

# PRINTING

	def print_image(self):
		op = Gtk.PrintOperation()
		# FIXME the preview doesn't work, i guess it's because of flatpak ?
		# I could connect to the 'preview' signal but that would be a hack
		op.connect('draw-page', self.do_draw_page)
		op.connect('begin-print', self.do_begin_print)
		op.connect('end-print', self.do_end_print)
		res = op.run(Gtk.PrintOperationAction.PRINT_DIALOG, self.window)

	def do_end_print(self, *args):
		pass

	def do_draw_page(self, op, print_ctx, page_num):
		# XXX TODO if it's too big for one page ?
		Gdk.cairo_set_source_pixbuf(print_ctx.get_cairo_context(), self.main_pixbuf, 0, 0)
		print_ctx.get_cairo_context().paint()

	def do_begin_print(self, op, print_ctx):
		op.set_n_pages(1)
		Gdk.cairo_set_source_pixbuf(print_ctx.get_cairo_context(), self.main_pixbuf, 0, 0)
		print_ctx.get_cairo_context().paint()

