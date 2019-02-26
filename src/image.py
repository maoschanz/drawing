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

from .properties import DrawingPropertiesDialog
from .utilities import utilities_save_pixbuf_at
from .utilities import utilities_show_overlay_on_context

@GtkTemplate(ui='/com/github/maoschanz/Drawing/ui/image.ui')
class DrawingImage(Gtk.Layout):
	__gtype_name__ = 'DrawingImage'

	def __init__(self, window, **kwargs):
		super().__init__(**kwargs)
		self.window = window
		self.init_template()

		self.gfile = None
		self.filename = None
		self.is_clicked = False
		self.build_tab_label()

		self.add_events( \
			Gdk.EventMask.BUTTON_PRESS_MASK | \
			Gdk.EventMask.BUTTON_RELEASE_MASK | \
			Gdk.EventMask.BUTTON_MOTION_MASK | \
			Gdk.EventMask.SMOOTH_SCROLL_MASK | \
			Gdk.EventMask.ENTER_NOTIFY_MASK | \
			Gdk.EventMask.LEAVE_NOTIFY_MASK)

		self.connect('draw', self.on_draw)
		self.connect('motion-notify-event', self.on_motion_on_area)
		self.connect('button-press-event', self.on_press_on_area)
		self.connect('button-release-event', self.on_release_on_area)
		self.connect('scroll-event', self.on_scroll_on_area)

		self.connect('enter-notify-event', self.on_enter_image)
		self.connect('leave-notify-event', self.on_leave_image)

	def init_image(self):
		"""Part of the initialization common to both a new blank image and an
		opened image."""
		self.undo_history = []
		self.redo_history = []
		self._is_saved = True
		self.scroll_x = 0
		self.scroll_y = 0
		self.selection_x = 1
		self.selection_y = 1
		self.selection_path = None

		self.update_history_sensitivity(False)
		self.use_stable_pixbuf()
		self.queue_draw()

	def build_tab_label(self):
		"""Build the "self.tab_title" attribute, which is the GTK widget
		displayed as the tab title."""
		self.tab_title = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, expand=True)
		self.tab_label = Gtk.Label(label=self.get_filename_for_display())
		self.tab_label.set_ellipsize(Pango.EllipsizeMode.END)
		btn = Gtk.Button.new_from_icon_name('window-close-symbolic', Gtk.IconSize.BUTTON)
		btn.set_relief(Gtk.ReliefStyle.NONE)
		btn.connect('clicked', self.try_close_tab)
		self.tab_title.pack_start(self.tab_label, expand=True, fill=True, padding=0)
		self.tab_title.pack_end(btn, expand=False, fill=False, padding=0)
		self.tab_title.show_all()

	def get_filename_for_display(self):
		if self.get_file_path() is None:
			unsaved_file_name = _("Untitled")
		else:
			unsaved_file_name = self.get_file_path().split('/')[-1]
		return unsaved_file_name

	def try_close_tab(self, *args):
		self.window.close_tab(self)
		self.destroy()
		self.main_pixbuf = None
		self.selection_pixbuf = None
		self.temp_pixbuf = None

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

	def restore_first_pixbuf(self):
		pixbuf = self.initial_operation['pixbuf']
		width = self.initial_operation['width']
		height = self.initial_operation['height']
		self.temp_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 1, 1) # XXX
		self.selection_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 1, 1) # XXX
		self.surface = cairo.ImageSurface(cairo.Format.ARGB32, width, height)
		if pixbuf is None:
			r = self.initial_operation['red']
			g = self.initial_operation['green']
			b = self.initial_operation['blue']
			a = self.initial_operation['alpha']
			self.main_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, width, height)
			cairo_context = cairo.Context(self.surface)
			cairo_context.set_source_rgba(r, g, b, a)
			cairo_context.paint()
			self.queue_draw()
			self.set_surface_as_stable_pixbuf()
		else:
			self.main_pixbuf = self.initial_operation['pixbuf'].copy()
			self.use_stable_pixbuf()

	def on_enter_image(self, *args):
		self.window.set_cursor(True)

	def on_leave_image(self, *args):
		self.window.set_cursor(False)

	# FILE MANAGEMENT

	def edit_properties(self):
		DrawingPropertiesDialog(self.window, self)

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
		self.tab_label.set_label(self.get_filename_for_display())

	def post_save(self):
		self._is_saved = True
		self.use_stable_pixbuf()
		self.queue_draw()

	# HISTORY MANAGEMENT

	def try_undo(self, *args):
		if self.window.operation_is_ongoing():
			self.window.active_tool().cancel_ongoing_operation()
		elif len(self.undo_history) != 0:
			self.redo_history.append(self.undo_history.pop())

	def try_redo(self, *args):
		self.undo_history.append(self.redo_history.pop())

	def update_history_sensitivity(self, tools_exist):
		if not tools_exist:
			can_undo = False
		else:
			can_undo = ( len(self.undo_history) != 0 ) or self.window.operation_is_ongoing()
		self.window.lookup_action('undo').set_enabled(can_undo)
		self.window.lookup_action('redo').set_enabled(len(self.redo_history) != 0)

	def add_operation_to_history(self, operation):
		self._is_saved = False
		self.undo_history.append(operation)
		self.update_history_sensitivity(True)

	def on_tool_finished(self):
		#self.redo_history = []
		self.update_history_sensitivity(True)
		self.queue_draw()
		self.set_surface_as_stable_pixbuf()
		self.active_tool().update_actions_state()

	# DRAWING OPERATIONS

	def on_draw(self, area, cairo_context):
		cairo_context.set_source_surface(self.get_surface(), \
			-1*self.scroll_x, -1*self.scroll_y)
		cairo_context.paint()

		if self.is_using_selection() and self.selection_pixbuf is not None:
			#print('image.py, line 163')
			utilities_show_overlay_on_context(cairo_context, self.get_dragged_selection_path(), True)

	def delete_former_selection(self):
		self.window.get_selection_tool().delete_temp()

	def on_press_on_area(self, area, event):
		if event.button == 2:
			self.is_clicked = False
			self.window.action_exchange_color()
			return
		self.is_clicked = True
		x, y = self.get_main_coord()
		self.active_tool().on_press_on_area(area, event, self.surface, \
			self.window.thickness_spinbtn.get_value(), \
			self.get_left_rgba(), self.get_right_rgba(), \
			x + event.x, y + event.y)

	def on_motion_on_area(self, area, event):
		if not self.is_clicked:
			return
		x, y = self.get_main_coord()
		event_x = x + event.x
		event_y = y + event.y
		self.active_tool().on_motion_on_area(area, event, self.surface, event_x, event_y)
		self.queue_draw()

	def on_release_on_area(self, area, event):
		if not self.is_clicked:
			return
		self.is_clicked = False
		x, y = self.get_main_coord()
		event_x = x + event.x
		event_y = y + event.y
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

	def get_main_coord(self, *args): # XXX utile ?
		return self.scroll_x, self.scroll_y

	def add_deltas(self, delta_x, delta_y, factor):
		self.scroll_x += int(delta_x * factor)
		self.scroll_y += int(delta_y * factor)
		self.correct_coords()
		self.window.minimap.update_minimap()

	def correct_coords(self):
		mpb_width = self.get_main_pixbuf().get_width()
		mpb_height = self.get_main_pixbuf().get_height()
		if self.scroll_x + self.get_allocated_width() > mpb_width:
			self.scroll_x = mpb_width - self.get_allocated_width()
		if self.scroll_y + self.get_allocated_height() > mpb_height:
			self.scroll_y = mpb_height - self.get_allocated_height()
		if self.scroll_x < 0:
			self.scroll_x = 0
		if self.scroll_y < 0:
			self.scroll_y = 0

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

	def get_selection_x(self):
		return self.selection_x

	def get_selection_y(self):
		return self.selection_y

	def get_dragged_selection_path(self):
		if self.selection_path is None:
			return None
		cairo_context = cairo.Context(self.get_surface())
		temp_x = self.window.get_selection_tool().temp_x
		temp_y = self.window.get_selection_tool().temp_y
		for pts in self.selection_path:
			if pts[1] is not ():
				x = pts[1][0] + self.selection_x - temp_x - self.scroll_x
				y = pts[1][1] + self.selection_y - temp_y - self.scroll_y
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

########################

	def get_surface(self):
		return self.surface

	def set_surface_as_stable_pixbuf(self):
		self.main_pixbuf = Gdk.pixbuf_get_from_surface(self.surface, 0, 0, \
			self.surface.get_width(), self.surface.get_height())

	def use_stable_pixbuf(self):
		self.surface = Gdk.cairo_surface_create_from_pixbuf(self.main_pixbuf, 0, None)

	def is_using_selection(self):
		return self.window.tool_needs_selection() and  self.window.active_tool().selection_is_active

# PRINTING XXX marche assez mal

	def print_image(self):
		op = Gtk.PrintOperation()
		op.connect('draw-page', self.do_draw_page)
		op.connect('begin-print', self.do_begin_print)
		op.connect('end-print', self.do_end_print)
		res = op.run(Gtk.PrintOperationAction.PRINT_DIALOG, self.window)

	def do_end_print(self, *args):
		pass

	def do_draw_page(self, op, print_ctx, page_num):
		Gdk.cairo_set_source_pixbuf(print_ctx.get_cairo_context(), self.main_pixbuf, 0, 0)
		print_ctx.get_cairo_context().paint()
		op.set_n_pages(1)

	def do_begin_print(self, op, print_ctx):
		Gdk.cairo_set_source_pixbuf(print_ctx.get_cairo_context(), self.main_pixbuf, 0, 0)
		print_ctx.get_cairo_context().paint()
		op.set_n_pages(1)
