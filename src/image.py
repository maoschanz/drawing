# image.py
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

import cairo, random, math
from gi.repository import Gtk, Gdk, Gio, GdkPixbuf, Pango, GLib
from .history_manager import DrHistoryManager
from .selection_manager import DrSelectionManager
from .properties import DrPropertiesDialog
from .utilities import InvalidFileFormatException
from .utilities_overlay import utilities_generic_canvas_outline

class DrMotionBehavior():
	_LIMIT = 10

	HOVER = 0
	DRAW = 1
	SLIP = 2

class NoPixbufNoChangeException(Exception):
	def __init__(self, pb_name):
		# Context: an error message
		message = _("New pixbuf empty, no change applied to %s")
		super().__init__(message % pb_name)

################################################################################

@Gtk.Template(resource_path='/com/github/maoschanz/drawing/ui/image.ui')
class DrImage(Gtk.Box):
	__gtype_name__ = 'DrImage'

	_drawing_area = Gtk.Template.Child()
	_h_scrollbar = Gtk.Template.Child()
	_v_scrollbar = Gtk.Template.Child()

	SCALE_FACTOR = 1.0 # XXX doesn't work well enough to be anything else

	def __init__(self, window, **kwargs):
		super().__init__(**kwargs)
		self.window = window

		self.gfile = None
		self.filename = None
		self._can_reload()

		self._fps_counter = 0
		self._skipped_frames = 0
		self._rendering_is_locked = False
		self._framerate_hint = 0
		self.reset_fps_counter()

		self._init_drawing_area()

		self._update_background_color()
		self.window.gsettings.connect('changed::ui-background-rgba', \
		                                          self._update_background_color)

		self._update_zoom_behavior()
		self.window.gsettings.connect('changed::ctrl-zoom', \
		                                             self._update_zoom_behavior)

	def _init_drawing_area(self):
		self._drawing_area.add_events( \
			Gdk.EventMask.BUTTON_PRESS_MASK | \
			Gdk.EventMask.BUTTON_RELEASE_MASK | \
			Gdk.EventMask.POINTER_MOTION_MASK | \
			Gdk.EventMask.SMOOTH_SCROLL_MASK | \
			Gdk.EventMask.ENTER_NOTIFY_MASK | \
			Gdk.EventMask.LEAVE_NOTIFY_MASK)
		# Using BUTTON_MOTION_MASK instead of POINTER_MOTION_MASK would be less
		# algorithmically complex but not "powerful" enough.

		# For displaying things on the widget
		self._drawing_area.connect('draw', self.on_draw)

		# For drawing with tools
		self._drawing_area.connect('motion-notify-event', self.on_motion_on_area)
		self._drawing_area.connect('button-press-event', self.on_press_on_area)
		self._drawing_area.connect('button-release-event', self.on_release_on_area)

		# For scrolling
		self._drawing_area.connect('scroll-event', self.on_scroll_on_area)
		self._h_scrollbar.connect('value-changed', self.on_scrollbar_value_change)
		self._v_scrollbar.connect('value-changed', self.on_scrollbar_value_change)

		# For the cursor
		self._drawing_area.connect('enter-notify-event', self.on_enter_image)
		self._drawing_area.connect('leave-notify-event', self.on_leave_image)

	def _update_background_color(self, *args):
		rgba = self.window.gsettings.get_strv('ui-background-rgba')
		self._bg_rgba = (float(rgba[0]), float(rgba[1]), \
		                                         float(rgba[2]), float(rgba[3]))
		# We remember this data here for performance: it will eb used by the
		# `on_draw` method which is called a lot, and reading a gsettings costs
		# a lot.

	def _update_zoom_behavior(self, *args):
		self._ctrl_to_zoom = self.window.gsettings.get_boolean('ctrl-zoom')

	############################################################################
	# Image initialization #####################################################

	def init_image_common(self):
		"""Part of the initialization common to both a new blank image and an
		opened image."""
		self._is_pressed = False

		# Zoom and scroll initialization
		self.scroll_x = 0
		self.scroll_y = 0
		self.set_zoom_level(100) # will do `self.zoom_level = 1.0`
		self.motion_behavior = DrMotionBehavior.HOVER
		self._slip_press_x = 0.0
		self._slip_press_y = 0.0
		self._slip_init_x = 0.0
		self._slip_init_y = 0.0

		# Selection initialization
		self.selection = DrSelectionManager(self)

		# History initialization
		self._history = DrHistoryManager(self)
		self.set_action_sensitivity('undo', False)
		self.set_action_sensitivity('redo', False)

	def init_background(self, width, height, background_rgba):
		self.init_image_common()
		self._history.set_initial_operation(background_rgba, None, width, height)
		self.restore_first_pixbuf()

	def try_load_pixbuf(self, pixbuf):
		self.init_image_common()
		self._load_pixbuf_common(pixbuf)
		self.restore_first_pixbuf()
		self.update_title()

	def _new_blank_pixbuf(self, w, h):
		return GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, w, h)

	def restore_first_pixbuf(self):
		"""Set the last saved pixbuf from the history as the main_pixbuf. This
		is used to rebuild the picture from its history."""
		last_saved_pixbuf_op = self._history.get_last_saved_state()

		# restore the state found in the history
		pixbuf = last_saved_pixbuf_op['pixbuf']
		width = last_saved_pixbuf_op['width']
		height = last_saved_pixbuf_op['height']
		self.set_temp_pixbuf(self._new_blank_pixbuf(1, 1))
		self.selection.init_pixbuf()
		self.surface = cairo.ImageSurface(cairo.Format.ARGB32, width, height)
		if pixbuf is None:
			# no pixbuf in the operation: the restored state is a blank one
			r = last_saved_pixbuf_op['red']
			g = last_saved_pixbuf_op['green']
			b = last_saved_pixbuf_op['blue']
			a = last_saved_pixbuf_op['alpha']
			self.set_main_pixbuf(self._new_blank_pixbuf(width, height))
			cairo_context = cairo.Context(self.surface)
			cairo_context.set_source_rgba(r, g, b, a)
			cairo_context.paint()
			self.update()
			self.set_surface_as_stable_pixbuf()
		else:
			self.set_main_pixbuf(last_saved_pixbuf_op['pixbuf'].copy())
			self.use_stable_pixbuf()

	############################################################################

	def _load_pixbuf_common(self, pixbuf):
		if not pixbuf.get_has_alpha():
			pixbuf = pixbuf.add_alpha(False, 255, 255, 255)
		background_rgba = self.window.gsettings.get_strv('default-rgba')
		self._history.set_initial_operation(background_rgba, pixbuf, \
		                                pixbuf.get_width(), pixbuf.get_height())
		self.set_main_pixbuf(pixbuf)

	def reload_from_disk(self):
		"""Safely reloads the image from the disk."""
		if self.gfile is None:
			# the action shouldn't be active in the first place
			return
		disk_pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.get_file_path())
		self._load_pixbuf_common(disk_pixbuf)
		self.window.set_picture_title(self.update_title())
		self.use_stable_pixbuf()
		self.update()
		self.remember_current_state()

	def try_load_file(self, gfile):
		try:
			self.gfile = gfile
			pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.get_file_path())
		except Exception as ex:
			if not ex.message:
				ex.message = "[exception without a valid message]"
			ex = InvalidFileFormatException(ex.message, gfile.get_path())
			self.window.prompt_message(True, ex.message)
			self.gfile = None
			pixbuf = self._new_blank_pixbuf(100, 100)
			# XXX dans l'idéal on devrait ne rien ouvrir non ? ou si besoin (si
			# ya pas de fenêtre) ouvrir un truc respectant les settings, plutôt
			# qu'un petit pixbuf corrompu
		self.try_load_pixbuf(pixbuf)
		self._can_reload()

	def _can_reload(self):
		self.set_action_sensitivity('reload_file', self.gfile is not None)

	############################################################################
	# Image title and tab management ###########################################

	def build_tab_widget(self):
		"""Build the GTK widget displayed as the tab title."""
		# The tab can be closed with a button.
		btn = Gtk.Button.new_from_icon_name('window-close-symbolic', Gtk.IconSize.BUTTON)
		btn.set_relief(Gtk.ReliefStyle.NONE)
		btn.connect('clicked', self.try_close_tab)
		# The title is a label. Middle-clicking on it closes the tab too.
		self.tab_label = Gtk.Label(label=self.get_filename_for_display())
		self.tab_label.set_ellipsize(Pango.EllipsizeMode.END)
		event_box = Gtk.EventBox()
		event_box.add(self.tab_label)
		event_box.connect('button-press-event', self.on_tab_title_clicked)
		# These widgets are packed in a regular box, which is returned.
		tab_title = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, expand=True)
		if self.window.deco_layout == 'he':
			tab_title.pack_start(btn, expand=False, fill=False, padding=0)
			tab_title.pack_end(event_box, expand=True, fill=True, padding=0)
		else:
			tab_title.pack_start(event_box, expand=True, fill=True, padding=0)
			tab_title.pack_end(btn, expand=False, fill=False, padding=0)
		tab_title.show_all()
		return tab_title
	
	def on_tab_title_clicked(self, widget, event_button):
		if event_button.type == Gdk.EventType.BUTTON_PRESS \
		and event_button.button == Gdk.BUTTON_MIDDLE:
			self.try_close_tab()
			return True
		return False # This callback HAS TO return a boolean

	def update_title(self):
		main_title = self.get_filename_for_display()
		if not self.is_saved():
			main_title = "*" + main_title
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
			self.selection.reset(False)
			self.main_pixbuf = None
			self.temp_pixbuf = None
			self._history.empty_history()
			return True
		else:
			return False

	def set_tab_label(self, title_text):
		self.tab_label.set_label(title_text)

	def get_file_path(self):
		if self.gfile is None:
			return None
		else:
			return self.gfile.get_path()

	def show_properties(self):
		DrPropertiesDialog(self.window, self)

	def update_image_wide_actions(self):
		self.update_history_sensitivity()
		self._can_reload()

	############################################################################
	# History management #######################################################

	def try_undo(self):
		self._history.try_undo()

	def try_redo(self):
		self._history.try_redo()

	def is_saved(self):
		return self._history.get_saved()

	def remember_current_state(self):
		self._history.add_state(self.main_pixbuf.copy())

	def update_history_sensitivity(self):
		self.set_action_sensitivity('undo', self._history.can_undo())
		self.set_action_sensitivity('redo', self._history.can_redo())
		# self.update_history_actions_labels()

	def add_to_history(self, operation):
		self._history.add_operation(operation)

	def should_replace(self):
		if self._history.can_undo():
			return False
		return not self._history.has_initial_pixbuf()

	def get_initial_rgba(self):
		operation = self._history.initial_operation
		r = operation['red']
		g = operation['green']
		b = operation['blue']
		a = operation['alpha']
		return Gdk.RGBA(red=r, green=g, blue=b, alpha=a)

	############################################################################
	# Misc ? ###################################################################

	def set_action_sensitivity(self, action_name, state):
		self.window.lookup_action(action_name).set_enabled(state)

	def update_actions_state(self):
		# XXX shouldn't it be done by the selection_manager?
		state = self.selection.is_active
		self.set_action_sensitivity('unselect', state)
		self.set_action_sensitivity('select_all', not state)
		self.set_action_sensitivity('selection_cut', state)
		self.set_action_sensitivity('selection_copy', state)
		self.set_action_sensitivity('selection_delete', state)
		self.set_action_sensitivity('selection_export', state)
		self.set_action_sensitivity('new_tab_selection', state)
		self.set_action_sensitivity('selection-replace-canvas', state)
		self.set_action_sensitivity('selection-expand-canvas', state)
		self.active_tool().update_actions_state()

	def active_tool(self):
		return self.window.active_tool()

	############################################################################
	# Drawing area, main pixbuf, and surface management ########################

	def reset_fps_counter(self, async_cb_data={}):
		"""Development only: live-display the evolution of the framerate of the
		drawing area. The max should be around 60, but many tools don't require
		so many redraws."""
		if self.window.should_track_framerate:
			# Context: this is a debug information that users will never see
			msg = _("%s frames per second") % self._fps_counter
			msg += " (" + str(self._skipped_frames) + " motion inputs skipped)"
			self.window.prompt_message(True, msg)
			self._fps_counter = 0
			self._skipped_frames = 0
			GLib.timeout_add(1000, self.reset_fps_counter, {})
		else:
			self.window.prompt_message(False, "")

	def on_draw(self, area, cairo_context):
		"""Signal callback. Executed when self._drawing_area is redrawn."""
		self._fps_counter += 1

		# Background color
		cairo_context.set_source_rgba(*self._bg_rgba)
		cairo_context.paint()

		# Zoom level
		cairo_context.scale(self.zoom_level, self.zoom_level)

		# Image (with scroll position)
		cairo_context.set_source_surface(self.get_surface(), \
		                                 -1 * self.scroll_x, -1 * self.scroll_y)
		cairo_context.paint()

		# What the tool shows on the canvas, upon what it paints, for example an
		# overlay to imply how to interact with a previewed operation.
		self.active_tool().on_draw_above(area, cairo_context)

		# Limit of the canvas (for readability)
		utilities_generic_canvas_outline(cairo_context, self.get_pixbuf_width(), \
		                              self.get_pixbuf_height(), self.zoom_level)

	def on_press_on_area(self, area, event):
		"""Signal callback. Executed when a mouse button is pressed on
		self._drawing_area, if the button is the mouse wheel the colors are
		exchanged, otherwise the signal is transmitted to the selected tool."""
		if self._is_pressed:
			# reject attempts to draw with a given button if an other one is
			# already doing something
			return
		event_x, event_y = self.get_event_coords(event)
		if event.button == 2:
			self.motion_behavior = DrMotionBehavior.SLIP
			self._slip_press_x = event.x
			self._slip_press_y = event.y
			self._slip_init_x = self.scroll_x
			self._slip_init_y = self.scroll_y
			return
		self.motion_behavior = DrMotionBehavior.DRAW
		self.active_tool().on_press_on_area(event, self.surface, event_x, event_y)
		self._is_pressed = True

	def on_motion_on_area(self, area, event):
		"""Signal callback. Executed when the mouse pointer moves upon
		self._drawing_area, the signal is transmitted to the selected tool.
		If a button (not the mouse wheel) is pressed, the tool's method should
		have an effect on the image, otherwise it shouldn't change anything
		except the mouse cursor icon for example."""

		if self.motion_behavior == DrMotionBehavior.HOVER:
			# Some tools need the coords in the image, others need the coords on
			# the widget, so the entire event is given.
			self.active_tool().on_unclicked_motion_on_area(event, self.surface)

		elif self.motion_behavior == DrMotionBehavior.DRAW:
			# implicitely impossible if not self._is_pressed
			event_x, event_y = self.get_event_coords(event)
			self.active_tool().on_motion_on_area(event, self.surface, event_x, \
			                                 event_y, self._rendering_is_locked)
			if self._rendering_is_locked:
				self._skipped_frames += 1
				return
			self._rendering_is_locked = True
			self.update()
			GLib.timeout_add(self._framerate_hint, self._async_unlock, {})

		else: # self.motion_behavior == DrMotionBehavior.SLIP:
			self.scroll_x = self._slip_init_x
			self.scroll_y = self._slip_init_y
			delta_x = self._slip_press_x - event.x
			delta_y = self._slip_press_y - event.y
			self.add_deltas(delta_x, delta_y, 1 / self.zoom_level)

	def on_release_on_area(self, area, event):
		"""Signal callback. Executed when a mouse button is released on
		self._drawing_area, if the button is not the signal is transmitted to
		the selected tool."""
		if self.motion_behavior == DrMotionBehavior.SLIP:
			if not self._is_slip_moving():
				self.window.on_middle_click()
			self.motion_behavior = DrMotionBehavior.HOVER
			return
		self.motion_behavior = DrMotionBehavior.HOVER
		event_x, event_y = self.get_event_coords(event)
		self.active_tool().on_release_on_area(event, self.surface, event_x, event_y)
		self.window.set_picture_title()
		self._is_pressed = False

	def _is_slip_moving(self):
		"""Tells if the pointer moved while the middle button of the mouse is
		pressed, depending on a constant hardcoded limit."""
		mx = abs(self._slip_init_x - self.scroll_x) > DrMotionBehavior._LIMIT
		my = abs(self._slip_init_y - self.scroll_y) > DrMotionBehavior._LIMIT
		return mx or my

	def update(self):
		# print('image.py: _drawing_area.queue_draw')
		self._drawing_area.queue_draw()

	def _async_unlock(self, content_params={}):
		self._rendering_is_locked = False

	def get_surface(self):
		return self.surface

	def on_enter_image(self, *args):
		self.window.set_cursor(True)

	def on_leave_image(self, *args):
		self.window.set_cursor(False)

	def post_save(self):
		self.use_stable_pixbuf()
		self.update()

	def set_surface_as_stable_pixbuf(self):
		w = self.surface.get_width()
		h = self.surface.get_height()
		self.main_pixbuf = Gdk.pixbuf_get_from_surface(self.surface, 0, 0, w, h)
		self._framerate_hint = math.sqrt(w * h) - 1000
		self._framerate_hint = int(self._framerate_hint * 0.2)
		# between 500 and 33ms (= between 2 and 30 fps)
		self._framerate_hint = max(33, min(500, self._framerate_hint))
		# print("image.py: hint =", self._framerate_hint)

	def use_stable_pixbuf(self):
		"""This is called by tools' `restore_pixbuf`, so at the beginning of
		each operation (even unapplied)."""
		# maybe the "scale" parameter should be 1 instead of 0
		self.surface = Gdk.cairo_surface_create_from_pixbuf(self.main_pixbuf, 0, None)
		# print('image.py: use_stable_pixbuf')
		self.surface.set_device_scale(self.SCALE_FACTOR, self.SCALE_FACTOR)

	def get_pixbuf_width(self):
		return self.main_pixbuf.get_width()

	def get_pixbuf_height(self):
		return self.main_pixbuf.get_height()

	def set_main_pixbuf(self, new_pixbuf):
		"""Safely set a pixbuf as the main one (not used everywhere internally
		in image.py, but it's normal)."""
		if new_pixbuf is None:
			raise NoPixbufNoChangeException('main_pixbuf')
		else:
			self.main_pixbuf = new_pixbuf

	############################################################################
	# Temporary pixbuf management ##############################################

	def set_temp_pixbuf(self, new_pixbuf):
		if new_pixbuf is None:
			raise NoPixbufNoChangeException('temp_pixbuf')
		else:
			self.temp_pixbuf = new_pixbuf

	def reset_temp(self):
		self.set_temp_pixbuf(self._new_blank_pixbuf(1, 1))
		self.use_stable_pixbuf()
		self.update()

	############################################################################
	# Interaction with the minimap #############################################

	def get_widget_width(self):
		return self._drawing_area.get_allocated_width()

	def get_widget_height(self):
		return self._drawing_area.get_allocated_height()

	def get_mini_pixbuf(self, preview_size):
		mpb_width = self.get_pixbuf_width()
		mpb_height = self.get_pixbuf_height()
		if mpb_height > mpb_width:
			mw = preview_size * (mpb_width/mpb_height)
			mh = preview_size
		else:
			mw = preview_size
			mh = preview_size * (mpb_height/mpb_width)
		return self.main_pixbuf.scale_simple(mw, mh, GdkPixbuf.InterpType.TILES)

	def get_show_overlay(self):
		mpb_width = self.get_pixbuf_width()
		mpb_height = self.get_pixbuf_height()
		show_x = self.get_widget_width() < mpb_width * self.zoom_level
		show_y = self.get_widget_height() < mpb_height * self.zoom_level
		show_overlay = show_x or show_y
		return show_overlay

	def get_minimap_ratio(self, mini_width):
		return mini_width/self.get_pixbuf_width()

	def get_visible_size(self):
		visible_width = int(self.get_widget_width() / self.zoom_level)
		visible_height = int(self.get_widget_height() / self.zoom_level)
		return visible_width, visible_height

	############################################################################
	# Scroll and zoom levels ###################################################

	def fake_scrollbar_update(self):
		self.add_deltas(0, 0, 0)

	def get_event_coords(self, event):
		event_x = self.scroll_x + (event.x / self.zoom_level)
		event_y = self.scroll_y + (event.y / self.zoom_level)
		return event_x, event_y

	def get_corrected_coords(self, x1, x2, y1, y2, with_selection, with_zoom):
		"""Do whatever coordinates conversions are needed by tools like `crop`
		and `scale` to display things (selection pixbuf, mouse cursors on hover,
		etc.) correctly enough."""
		w = x2 - x1
		h = y2 - y1
		x1 = x1 - self.scroll_x
		y1 = y1 - self.scroll_y
		if with_selection:
			x1 += self.selection.selection_x
			y1 += self.selection.selection_y
		x2 = x1 + w
		y2 = y1 + h
		if with_zoom:
			x1 *= self.zoom_level
			x2 *= self.zoom_level
			y1 *= self.zoom_level
			y2 *= self.zoom_level
		return x1, x2, y1, y2

	def get_nineths_sizes(self, apply_to_selection, x1, y1):
		"""Returns the sizes of the 'nineths' of the image used for example by
		'scale' or 'crop' to decide the cursor they'll show."""
		height = self.temp_pixbuf.get_height()
		width = self.temp_pixbuf.get_width()
		if not apply_to_selection:
			x1 = 0
			y1 = 0
		# width_left, width_right, height_top, height_bottom
		wl, wr, ht, hb = self.get_corrected_coords(x1, width, y1, height, \
		                                               apply_to_selection, True)
		# FIXME using local deltas this way "works" but isn't mathematically
		# correct: scaled selections have a "null" and excentred central nineth
		# ^ c'est vrai ça ??
		wl += 0.4 * width * self.zoom_level
		wr -= 0.4 * width * self.zoom_level
		ht += 0.4 * height * self.zoom_level
		hb -= 0.4 * height * self.zoom_level
		return wl, wr, ht, hb

	def on_scroll_on_area(self, area, event):
		# TODO https://lazka.github.io/pgi-docs/index.html#Gdk-3.0/classes/EventScroll.html#Gdk.EventScroll
		ctrl_is_used = (event.state & Gdk.ModifierType.CONTROL_MASK) == Gdk.ModifierType.CONTROL_MASK
		if ctrl_is_used == self._ctrl_to_zoom:
			self._zoom_to_point(event)
		else:
			self.add_deltas(event.delta_x, event.delta_y, 10)

	def on_scrollbar_value_change(self, scrollbar):
		self.correct_coords(self._h_scrollbar.get_value(), self._v_scrollbar.get_value())
		self.update() # allowing imperfect framerate would likely be useless

	def add_deltas(self, delta_x, delta_y, factor):
		wanted_x = self.scroll_x + int(delta_x * factor)
		wanted_y = self.scroll_y + int(delta_y * factor)
		self.correct_coords(wanted_x, wanted_y)
		self.window.minimap.update_minimap(False)

	def correct_coords(self, wanted_x, wanted_y):
		available_w = self.get_widget_width()
		available_h = self.get_widget_height()
		if available_w < 2:
			return # could be better handled

		# Update the horizontal scrollbar
		mpb_width = self.get_pixbuf_width()
		wanted_x = min(wanted_x, self.get_max_coord(mpb_width, available_w))
		wanted_x = max(wanted_x, 0)
		self.update_scrollbar(False, available_w, int(mpb_width), int(wanted_x))

		# Update the vertical scrollbar
		mpb_height = self.get_pixbuf_height()
		wanted_y = min(wanted_y, self.get_max_coord(mpb_height, available_h))
		wanted_y = max(wanted_y, 0)
		self.update_scrollbar(True, available_h, int(mpb_height), int(wanted_y))

	def get_max_coord(self, mpb_size, available_size):
		max_coord = mpb_size - (available_size / self.zoom_level)
		return max_coord

	def update_scrollbar(self, is_vertical, allocated_size, pixbuf_size, coord):
		if is_vertical:
			scrollbar = self._v_scrollbar
		else:
			scrollbar = self._h_scrollbar
		scrollbar.set_visible(allocated_size / self.zoom_level < pixbuf_size)
		scrollbar.set_range(0, pixbuf_size)
		scrollbar.get_adjustment().set_page_size(allocated_size / self.zoom_level)
		scrollbar.set_value(coord)
		if is_vertical:
			self.scroll_y = int(scrollbar.get_value())
		else:
			self.scroll_x = int(scrollbar.get_value())

	def _zoom_to_point(self, event):
		"""Zoom in or out the image in a way such that the point under the
		pointer stays as much as possible under the pointer."""
		event_x, event_y = self.get_event_coords(event)

		zoom_delta = (event.delta_x + event.delta_y) * -4 # Arbitrary
		self.inc_zoom_level(zoom_delta)

		# Where the zoom event occurs, in terms of percentages, in the widget's
		# reference frame. Like, "at 10% of the width, and 80% of the height".
		proportion_w = event.x / self.get_widget_width()
		proportion_h = event.y / self.get_widget_height()

		# Size of the rectangle between the current scroll position (values of
		# the self.scroll_* attributes) and the zoom event. Both are expressed
		# in pixels in the reference frame of the pixbuf.
		corner_w = event_x - self.scroll_x
		corner_h = event_y - self.scroll_y

		# Dark magic based on unsound experiments XXX
		fake_delta_x = corner_w * (proportion_w - 0.5)
		fake_delta_y = corner_h * (proportion_h - 0.5)
		if zoom_delta > 0:
			# Zooming in
			fake_delta_x *= 0.5
			fake_delta_y *= 0.5
		else:
			# Zooming out
			fake_delta_x *= -0.1
			fake_delta_y *= -0.1

		# Updating the scroll position based on the values previously found
		self.add_deltas(fake_delta_x, fake_delta_y, 1)

	def inc_zoom_level(self, delta):
		self.set_zoom_level((self.zoom_level * 100) + delta)

	def set_zoom_level(self, level):
		normalized_zoom_level = max(min(level, 400), 20)
		self.zoom_level = (int(normalized_zoom_level)/100)
		self.window.minimap.update_zoom_scale(self.zoom_level)
		self.fake_scrollbar_update()
		self.update()

	def set_opti_zoom_level(self, *args):
		allocated_width = self.get_widget_width()
		allocated_height = self.get_widget_height()
		h_ratio = allocated_width / self.get_pixbuf_width()
		v_ratio = allocated_height / self.get_pixbuf_height()
		opti = min(h_ratio, v_ratio) * 99 # Not 100 because some margin is cool
		self.set_zoom_level(opti)
		self.scroll_x = 0
		self.scroll_y = 0

	############################################################################
################################################################################

