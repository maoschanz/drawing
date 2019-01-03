# pixbuf_manager.py
#
# Copyright 2018 Romain F. T.
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

from gi.repository import Gtk, Gdk, Gio, GdkPixbuf, GLib
import cairo

# This object contains methods related to pixbufs and cairo surfaces manipulation.
# It includes everything related to the history, the selection, the clipboard,
# resizing pictures or scaling or rotating them.
class DrawingPixbufManager():

	def __init__(self, window):
		self.window = window

		width = self.window._settings.get_int('default-width')
		height = self.window._settings.get_int('default-height')

		self.gfile = None
		self.clipboard = None

		self.selection_x = 1
		self.selection_y = 1
		self._path = None
		self.selection_is_active = False
		self.temp_x = 1
		self.temp_y = 1

		# INIT PIXBUFS AND SURFACES

		# self.full_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, width, height) # 8 ??? les autres plantent
		self.main_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, width, height) # 8 ??? les autres plantent
		self.selection_pixbuf = None
		self.temp_pixbuf = None

		self.surface = cairo.ImageSurface(cairo.Format.ARGB32, width, height)

		# INIT HISTORY

		self.undo_history = []
		self.redo_history = []

	def is_empty_picture(self):
		if self.gfile is None and not self.can_undo():
			return True
		else:
			return False

	def initial_save(self, fn):
		self.gfile = Gio.File.new_for_path(fn)
		self.use_stable_pixbuf()

	def load_main_from_filename(self, filename):
		self.main_pixbuf = GdkPixbuf.Pixbuf.new_from_file(filename)

	def save_pixbuf_to_filename(self, filename):
		self.main_pixbuf = Gdk.pixbuf_get_from_surface(self.surface, 0, 0, \
			self.surface.get_width(), self.surface.get_height())
		(pb_format, width, height) = GdkPixbuf.Pixbuf.get_file_info(filename)
		if pb_format is None: # "jpeg", "png", "tiff", "ico" or "bmp"
			self.main_pixbuf.savev(filename, filename.split('.')[-1], [None], [])
		else:
			self.main_pixbuf.savev(filename, pb_format.get_name(), [None], [])
		# TODO la doc propose une fonction d'enregistrement avec callback pour faire ce que je veux

	def export_main_as(self, file_format):
		file_path = self.window.run_save_file_chooser(file_format)
		if file_path is not None:
			self.main_pixbuf.savev(file_path, file_format, [None], [])

	def crop_main_surface(self, x, y, width, height):
		x = int(x)
		y = int(y)
		width = int(width)
		height = int(height)

		# The GdkPixbuf.Pixbuf.copy_area method works only when expanding the size
		max_width = max(width, self.surface.get_width())
		max_height = max(height, self.surface.get_height())
		new_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, max_width, max_height)
		self.main_pixbuf.copy_area(0, 0, self.surface.get_width(), self.surface.get_height(), new_pixbuf, 0, 0)
		self.main_pixbuf = new_pixbuf

		# The cairo.Surface.map_to_image method works only when reducing the size
		self.surface = Gdk.cairo_surface_create_from_pixbuf(self.main_pixbuf, 0, None)
		self.surface = self.surface.map_to_image(cairo.RectangleInt(x, y, width, height))
		self.main_pixbuf = Gdk.pixbuf_get_from_surface(self.surface, 0, 0, \
			self.surface.get_width(), self.surface.get_height())

		if x != 0 or y != 0:
			self.crop_main_surface(0, 0, width, height)

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

	def on_tool_finished(self):
		self.undo_history.append(self.main_pixbuf.copy())
		self.redo_history = []
		self.window.update_history_sensitivity()
		self.window.drawing_area.queue_draw()
		self.set_pixbuf_as_stable()
		self.selection_is_active = False
		self.update_selection_actions()

	def can_undo(self):
		if len(self.undo_history) == 0:
			return False
		else:
			return True

	def can_redo(self):
		if len(self.redo_history) == 0:
			return False
		else:
			return True

	def set_pixbuf_as_stable(self):
		self.main_pixbuf = Gdk.pixbuf_get_from_surface(self.surface, 0, 0, \
			self.surface.get_width(), self.surface.get_height())

	def use_stable_pixbuf(self):
		self.surface = Gdk.cairo_surface_create_from_pixbuf(self.main_pixbuf, 0, None)

	def undo_operation(self):
		self.redo_history.append(self.main_pixbuf.copy())
		self.main_pixbuf = self.undo_history.pop()
		self.use_stable_pixbuf()

	def redo_operation(self):
		self.undo_history.append(self.main_pixbuf.copy())
		self.main_pixbuf = self.redo_history.pop()
		self.use_stable_pixbuf()

	def delete_operation(self):
		x0 = self.selection_x
		y0 = self.selection_y
		x1 = x0 + self.selection_pixbuf.get_width()
		y1 = y0 + self.selection_pixbuf.get_height()
		w_context = cairo.Context(self.surface)
		w_context.move_to(x1, y1)
		w_context.line_to(x1, y0)
		w_context.line_to(x0, y0)
		w_context.line_to(x0, y1)
		w_context.close_path()
		w_context.clip()
		w_context.set_operator(cairo.Operator.CLEAR)
		w_context.paint()
		w_context.set_operator(cairo.Operator.OVER)

	def cut_operation(self):
		self.copy_operation()
		self.reset_selection()
		self.delete_temp()

	def copy_operation(self):
		cb = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
		cb.set_image(self.selection_pixbuf)

	def paste_operation(self):
		cb = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
		self.selection_pixbuf = cb.wait_for_image()
		self.show_selection_rectangle()
		self.create_selection_from_selection()

	def create_free_selection_from_main(self, cairo_path):
		self.selection_pixbuf = self.main_pixbuf.copy()
		surface = Gdk.cairo_surface_create_from_pixbuf(self.selection_pixbuf, 0, None)
		xmin, ymin = surface.get_width(), surface.get_height()
		xmax, ymax = 0.0, 0.0
		for pts in cairo_path:
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
		w_context.append_path(cairo_path)
		w_context.fill()
		w_context.set_operator(cairo.Operator.OVER)
		self.selection_pixbuf = Gdk.pixbuf_get_from_surface(surface, xmin, ymin, \
			xmax - xmin, ymax - ymin)
		self.set_temp(cairo_path)

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
		temp_surface = Gdk.cairo_surface_create_from_pixbuf(self.main_pixbuf, 0, None)
		temp_surface = temp_surface.map_to_image(cairo.RectangleInt(x0, y0, w, h))
		self.selection_pixbuf = Gdk.pixbuf_get_from_surface(temp_surface, 0, 0, \
			temp_surface.get_width(), temp_surface.get_height())
		w_context = cairo.Context(self.surface)
		w_context.move_to(x0, y0)
		w_context.line_to(x1, y0)
		w_context.line_to(x1, y1)
		w_context.line_to(x0, y1)
		w_context.close_path()
		selection_path = w_context.copy_path()
		self.set_temp(selection_path)

	def create_selection_from_selection(self):
		self.selection_is_active = True
		self.temp_pixbuf = None
		self.update_selection_actions()

	def set_temp(self, selection_path):
		self._path = selection_path
		self.temp_x = self.selection_x
		self.temp_y = self.selection_y
		self.temp_pixbuf = self.selection_pixbuf.copy()
		self.selection_is_active = True
		self.update_selection_actions()

	def delete_temp(self):
		if self.temp_pixbuf is None:
			return
		w_context = cairo.Context(self.surface)
		w_context.new_path()
		w_context.append_path(self._path)
		w_context.clip()
		w_context.set_operator(cairo.Operator.CLEAR)
		w_context.paint()
		w_context.set_operator(cairo.Operator.OVER)

	def show_selection_rectangle(self):
		self.use_stable_pixbuf()
		if self.selection_is_active:
			self.delete_temp()
		self.show_selection_content()
		self.show_overlay_on_surface(self.surface, self._path, True)

	# FIXME le path n'est pas bon quand on a scale ou crop la sélection
	def show_overlay_on_surface(self, surface, cairo_path, is_selection):
		w_context = cairo.Context(surface)
		w_context.new_path()
		if is_selection:
			w_context.set_dash([3, 3])
			dragged_path = self.get_dragged_selection_path(surface, cairo_path)
			w_context.append_path(dragged_path)
		else:
			w_context.append_path(cairo_path)
		w_context.clip_preserve()
		w_context.set_source_rgba(0.1, 0.1, 0.3, 0.2)
		w_context.paint()
		w_context.set_source_rgba(0.5, 0.5, 0.5, 0.5)
		w_context.stroke()

	def get_dragged_selection_path(self, surface, cairo_path):
		w_context = cairo.Context(surface)
		for pts in cairo_path:
			if pts[1] is not ():
				x = pts[1][0] + self.selection_x - self.temp_x
				y = pts[1][1] + self.selection_y - self.temp_y
				w_context.line_to(int(x), int(y))
		w_context.close_path()
		return w_context.copy_path()

	def show_selection_content(self):
		if self.selection_pixbuf is None:
			return
		w_context = cairo.Context(self.surface)
		Gdk.cairo_set_source_pixbuf(w_context, self.selection_pixbuf, self.selection_x, self.selection_y)
		w_context.paint()

	def reset_selection(self):
		self.selection_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 1, 1) # 8 ??? les autres plantent
		self.use_stable_pixbuf()
		self.selection_is_active = False
		self.update_selection_actions()

	def select_all(self):
		self.selection_x = 0
		self.selection_y = 0
		self.selection_pixbuf = self.main_pixbuf.copy()
		w_context = cairo.Context(self.surface)
		w_context.move_to(0, 0)
		w_context.line_to(self.main_pixbuf.get_width(), 0)
		w_context.line_to(self.main_pixbuf.get_width(), self.main_pixbuf.get_height())
		w_context.line_to(0, self.main_pixbuf.get_height())
		w_context.close_path()
		selection_path = w_context.copy_path()
		self.set_temp(selection_path)
		self.show_selection_rectangle()

	def export_selection_as(self):
		file_path = self.window.run_save_file_chooser('')
		if file_path is not None:
			self.selection_pixbuf.savev(file_path, file_path.split('.')[-1], [None], [])

	def update_selection_actions(self):
		self.window.active_tool().update_actions_state()

	def point_is_in_selection(self, x, y):
		dragged_path = self.get_dragged_selection_path(self.surface, self._path)
		w_context = cairo.Context(self.surface)
		w_context.new_path()
		w_context.append_path(dragged_path)
		return w_context.in_fill(x, y)

	def scale_pixbuf_to(self, is_selection, new_width, new_height):
		if is_selection:
			self.selection_pixbuf = self.selection_pixbuf.scale_simple(new_width, new_height, GdkPixbuf.InterpType.TILES)
			self.show_selection_rectangle()
		else:
			self.main_pixbuf = self.main_pixbuf.scale_simple(new_width, new_height, GdkPixbuf.InterpType.TILES)
			self.use_stable_pixbuf()
			self.on_tool_finished()
