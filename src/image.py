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

from .utilities import utilities_save_pixbuf_at
from .selection_manager import DrawingSelectionManager

class DrawingMotionBehavior():
	HOVER = 0
	DRAW = 1
	SLIP = 2

################################################################################

@Gtk.Template(resource_path='/com/github/maoschanz/drawing/ui/image.ui')
class DrawingImage(Gtk.Box):
	__gtype_name__ = 'DrawingImage'

	drawing_area = Gtk.Template.Child()
	h_scrollbar = Gtk.Template.Child()
	v_scrollbar = Gtk.Template.Child()

	CLOSING_PRECISION = 10

	def __init__(self, window, **kwargs):
		super().__init__(**kwargs)
		self.window = window

		self.gfile = None
		self.filename = None

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
		# [Option] automatic zoom level
		self.drawing_area.connect('size-allocate', self.set_opti_zoom_level)

		self.ctrl_to_zoom = self.window._settings.get_string('zoom-behavior') == 'ctrl'

	############################################################################
	# Image initialization #####################################################

	def init_image(self):
		"""Part of the initialization common to both a new blank image and an
		opened image."""
		self._is_pressed = False

		# Zoom and scroll initialization
		self.zoom_level = 1.0
		self.scroll_x = 0
		self.scroll_y = 0
		self.motion_behavior = DrawingMotionBehavior.HOVER
		self.press2_x = 0.0
		self.press2_y = 0.0
		self.drag_scroll_x = 0.0
		self.drag_scroll_y = 0.0
		self.zoom_is_auto = self.window._settings.get_boolean('auto-zoom')
		# TODO peut être updaté quand la valeur de la clef change

		# Selection initialization
		self.selection = DrawingSelectionManager(self)
		
		# History initialization
		self.previous_pixbuf = None
		self.undo_history = []
		self.redo_history = []
		self._is_saved = True
		self.window.lookup_action('undo').set_enabled(False)
		self.window.lookup_action('redo').set_enabled(False)

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
		self.init_image()
		self.restore_first_pixbuf()

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
		self.init_image()
		self.restore_first_pixbuf()
		self.update_title()

	def restore_first_pixbuf(self):
		"""Set the first saved pixbuf as the main_pixbuf. This is used to
		rebuild the picture from its history."""
		pixbuf = self.initial_operation['pixbuf']
		width = self.initial_operation['width']
		height = self.initial_operation['height']
		self.temp_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 1, 1)
		self.selection.init_pixbuf()
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
		self.init_image()
		self.restore_first_pixbuf()
		self.update_title()

	############################################################################
	# Image title and tab management ###########################################

	def build_tab_widget(self):
		"""Build the GTK widget displayed as the tab title."""
		self.tab_label = Gtk.Label(label=self.get_filename_for_display())
		self.tab_label.set_ellipsize(Pango.EllipsizeMode.END)
		return self.build_title_widget_common(self.tab_label)

	def build_title_widget_common(self, self_label):
		# "common" because it could be nice to have a epiphany-like menu
		tab_title = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, expand=True)
		btn = Gtk.Button.new_from_icon_name('window-close-symbolic', Gtk.IconSize.BUTTON)
		btn.set_relief(Gtk.ReliefStyle.NONE)
		btn.connect('clicked', self.try_close_tab)
		if self.window.decorations == 'csd-eos':
			tab_title.pack_start(btn, expand=False, fill=False, padding=0)
			tab_title.pack_end(self_label, expand=True, fill=True, padding=0)
		else:
			tab_title.pack_start(self_label, expand=True, fill=True, padding=0)
			tab_title.pack_end(btn, expand=False, fill=False, padding=0)
		tab_title.show_all()
		return tab_title

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
			self.selection.reset()
			self.main_pixbuf = None
			self.temp_pixbuf = None
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

	############################################################################
	# History management #######################################################

	def try_undo(self, *args):
		# TODO implement operation_is_ongoing
		# if self.window.operation_is_ongoing():
		# 	self.active_tool().cancel_ongoing_operation()
		# elif len(self.undo_history) != 0:
		# 	self.redo_history.append(self.undo_history.pop())
		self.active_tool().cancel_ongoing_operation()
		if len(self.undo_history) != 0:
			self.redo_history.append(self.undo_history.pop())
		if self.previous_pixbuf is not None:
			self.main_pixbuf = self.previous_pixbuf
			self.previous_pixbuf = None
			self.use_stable_pixbuf()
			self.update()
			self.update_history_sensitivity()
		else:
			self.rebuild_from_history()

	def try_redo(self, *args):
		operation = self.redo_history.pop()
		self.window.tools[operation['tool_id']].apply_operation(operation)

	def rebuild_from_history(self):
		self.restore_first_pixbuf()
		history = self.undo_history.copy()
		self.undo_history = []
		for op in history:
			# print(op)
			self.window.tools[op['tool_id']].simple_apply_operation(op)
		self.update()
		self.update_history_sensitivity()

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

	def add_pixbuf_to_history(self):
		# self.previous_pixbuf = self.main_pixbuf.copy()
		pass # TODO

	def add_to_history(self, operation):
		self.set_surface_as_stable_pixbuf()
		# print('add_operation_to_history')
		# print(operation['tool_id'])
		# if operation['tool_id'] == 'select':
		#	print(operation['operation_type'])
		# print('-----------------------------------')
		self._is_saved = False
		self.undo_history.append(operation)

	############################################################################
	# Misc ? ###################################################################

	def set_action_sensitivity(self, action_name, state):
		self.window.lookup_action(action_name).set_enabled(state)

	def update_actions_state(self):
		state = self.selection.is_active
		self.set_action_sensitivity('unselect', state)
		self.set_action_sensitivity('selection_cut', state)
		self.set_action_sensitivity('selection_copy', state)
		self.set_action_sensitivity('selection_delete', state)
		self.set_action_sensitivity('selection_export', state)
		self.set_action_sensitivity('new_tab_selection', state)
		self.active_tool().update_actions_state()

	def active_tool(self):
		return self.window.active_tool()

	############################################################################
	# Drawing area, main pixbuf, and surface management ########################

	def on_draw(self, area, cairo_context):
		"""Signal callback. Executed when self.drawing_area is redrawn."""
		cairo_context.scale(self.zoom_level, self.zoom_level)
		cairo_context.set_source_surface(self.get_surface(), \
		                                 -1 * self.scroll_x, -1 * self.scroll_y)
		cairo_context.paint()

		self.active_tool().on_draw(area, cairo_context)

	def on_press_on_area(self, area, event):
		"""Signal callback. Executed when a mouse button is pressed on
		self.drawing_area, if the button is the mouse wheel the colors are
		exchanged, otherwise the signal is transmitted to the selected tool."""
		if self._is_pressed:
			return
		event_x, event_y = self.get_event_coords(event)
		if event.button == 2:
			self.motion_behavior = DrawingMotionBehavior.SLIP
			self.press2_x = event_x
			self.press2_y = event_y
			self.drag_scroll_x = event_x
			self.drag_scroll_y = event_y
			return
		self.motion_behavior = DrawingMotionBehavior.DRAW
		self.active_tool().on_press_on_area(event, self.surface, event_x, event_y)
		self._is_pressed = True

	def on_motion_on_area(self, area, event):
		"""Signal callback. Executed when the mouse pointer moves upon
		self.drawing_area, the signal is transmitted to the selected tool.
		If a button (not the mouse wheel) is pressed, the tool's method should
		have an effect on the image, otherwise it shouldn't change anything
		except the mouse cursor icon for example."""
		event_x, event_y = self.get_event_coords(event)
		if self.motion_behavior == DrawingMotionBehavior.HOVER:
			# XXX ça apprécierait sans doute d'avoir direct les bonnes coordonnées ?
			self.active_tool().on_unclicked_motion_on_area(event, self.surface)
		elif self.motion_behavior == DrawingMotionBehavior.DRAW:
			# implicitely impossible if not self._is_pressed
			self.active_tool().on_motion_on_area(event, self.surface, event_x, event_y)
			self.update()
		else: # self.motion_behavior == DrawingMotionBehavior.SLIP:
			delta_x = int(self.drag_scroll_x - event_x)
			delta_y = int(self.drag_scroll_y - event_y)
			self.add_deltas(delta_x, delta_y, 0.8)
			self.drag_scroll_x = event_x
			self.drag_scroll_y = event_y

	def on_release_on_area(self, area, event):
		"""Signal callback. Executed when a mouse button is released on
		self.drawing_area, if the button is not the signal is transmitted to the
		selected tool."""
		if self.motion_behavior == DrawingMotionBehavior.SLIP:
			if abs(self.press2_x - self.drag_scroll_x) < self.CLOSING_PRECISION \
			and abs(self.press2_y - self.drag_scroll_y) < self.CLOSING_PRECISION:
				self.window.on_middle_click(event)
			self.motion_behavior = DrawingMotionBehavior.HOVER
			return
		self.motion_behavior = DrawingMotionBehavior.HOVER
		event_x, event_y = self.get_event_coords(event)
		self.active_tool().on_release_on_area(event, self.surface, event_x, event_y)
		self.window.set_picture_title()
		self._is_pressed = False

	def update(self):
		self.drawing_area.queue_draw()

	def get_surface(self):
		return self.surface

	def on_enter_image(self, *args):
		self.window.set_cursor(True)

	def on_leave_image(self, *args):
		self.window.set_cursor(False)

	def post_save(self):
		self._is_saved = True
		self.use_stable_pixbuf()
		self.update()

	def set_surface_as_stable_pixbuf(self):
		# print('image/379: set_surface_as_stable_pixbuf')
		self.main_pixbuf = Gdk.pixbuf_get_from_surface(self.surface, 0, 0, \
		                    self.surface.get_width(), self.surface.get_height())

	def use_stable_pixbuf(self):
		# print('image/384: use_stable_pixbuf')
		self.surface = Gdk.cairo_surface_create_from_pixbuf(self.main_pixbuf, 0, None)

	def get_main_pixbuf(self):
		return self.main_pixbuf

	def get_pixbuf_width(self):
		return self.main_pixbuf.get_width()

	def get_pixbuf_height(self):
		return self.main_pixbuf.get_height()

	def set_main_pixbuf(self, new_pixbuf):
		if new_pixbuf is None:
			# FIXME wtf, throw something maybe???
			return False
		else:
			self.main_pixbuf = new_pixbuf
			return True

	############################################################################
	# Temporary pixbuf management ##############################################

	def get_temp_pixbuf(self):
		return self.temp_pixbuf

	def set_temp_pixbuf(self, new_pixbuf):
		if new_pixbuf is None:
			return False
		else:
			self.temp_pixbuf = new_pixbuf
			return True

	def reset_temp(self):
		self.temp_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 1, 1)
		self.use_stable_pixbuf()
		self.update()

	############################################################################
	# Interaction with the minimap #############################################

	def get_widget_width(self):
		return self.drawing_area.get_allocated_width()

	def get_widget_height(self):
		return self.drawing_area.get_allocated_height()

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

	def on_scroll_on_area(self, area, event):
		# TODO https://lazka.github.io/pgi-docs/index.html#Gdk-3.0/classes/EventScroll.html#Gdk.EventScroll
		ctrl_is_used = (event.state & Gdk.ModifierType.CONTROL_MASK) == Gdk.ModifierType.CONTROL_MASK
		if ctrl_is_used == self.ctrl_to_zoom:
			event_x, event_y = self.get_event_coords(event)
			self.zoom_to_point(event.delta_x, event.delta_y, event.x, event.y)
		else:
			self.add_deltas(event.delta_x, event.delta_y, 10)

	def on_scrollbar_value_change(self, scrollbar):
		self.correct_coords(self.h_scrollbar.get_value(), self.v_scrollbar.get_value())
		self.update()

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
			scrollbar = self.v_scrollbar
		else:
			scrollbar = self.h_scrollbar
		scrollbar.set_visible(allocated_size / self.zoom_level < pixbuf_size)
		scrollbar.set_range(0, pixbuf_size)
		scrollbar.get_adjustment().set_page_size(allocated_size / self.zoom_level)
		scrollbar.set_value(coord)
		if is_vertical:
			self.scroll_y = int(scrollbar.get_value())
		else:
			self.scroll_x = int(scrollbar.get_value())

	def zoom_to_point(self, delta_x, delta_y, x, y):
		zoom_delta = (delta_x + delta_y) * -5
		self.inc_zoom_level(zoom_delta)
		displayed_w = self.get_widget_width() / self.zoom_level
		displayed_h = self.get_widget_height() / self.zoom_level
		fake_delta_x = x - (displayed_w / 2)
		fake_delta_y = y - (displayed_h / 2)
		self.add_deltas(fake_delta_x, fake_delta_y, min(1, 1/self.zoom_level))

	def inc_zoom_level(self, delta):
		self.set_zoom_level((self.zoom_level * 100) + delta)

	def set_zoom_level(self, level):
		self.zoom_level = (int(level)/100)
		self.window.minimap.update_zoom_scale(self.zoom_level)
		self.fake_scrollbar_update()
		self.update()

	def set_opti_zoom_level(self, *args):
		if not self.zoom_is_auto:
			return
		allocated_width = self.get_widget_width()
		allocated_height = self.get_widget_height()
		if allocated_width == 1:
			# FIXME because self.drawing_area might be not allocated yet
			return
			# allocated_width = 800
			# allocated_height = 400
			# FIXME but that hack can't update the minimap label
		h_ratio = allocated_width / self.get_pixbuf_width()
		v_ratio = allocated_height / self.get_pixbuf_height()
		opti = min(h_ratio, v_ratio) * 99 # Not 100 because some margin is cool
		self.set_zoom_level(opti)
		self.scroll_x = 0
		self.scroll_y = 0

	############################################################################
	# Printing operations ######################################################

	def print_image(self):
		op = Gtk.PrintOperation()
		# FIXME the preview doesn't work, i guess it's because of flatpak ?
		# I could connect to the 'preview' signal but that would be weird
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

	############################################################################
################################################################################

