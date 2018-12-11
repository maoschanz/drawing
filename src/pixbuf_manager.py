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

class DrawingPixbufManager():

	def __init__(self, window):
		self.window = window

		width = self.window._settings.get_int('default-width')
		height = self.window._settings.get_int('default-height')
		self.preview_size = self.window._settings.get_int('preview-size')

		self.clipboard = None

		self.selection_x = 1
		self.selection_y = 1
		self.selection_is_active = False
		self.temp_x = 1
		self.temp_y = 1

		# INIT PIXBUFS AND SURFACES

		# self.full_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, width, height) # 8 ??? les autres plantent
		self.main_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, width, height) # 8 ??? les autres plantent
		self.mini_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 300, 300) # 8 ??? les autres plantent
		self.selection_pixbuf = None
		self.temp_pixbuf = None

		self.surface = cairo.ImageSurface(cairo.Format.ARGB32, width, height)
		self.mini_surface = cairo.ImageSurface(cairo.Format.ARGB32, 5, 5)

		# INIT HISTORY

		self.undo_history = []
		self.redo_history = []

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

	def resize_main_surface(self, x, y, width, height):
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

		self.window.drawing_area.set_size(width, height)
		if x != 0 or y != 0:
			self.resize_main_surface(0, 0, width, height)

	def on_tool_finished(self):
		self.undo_history.append(self.main_pixbuf.copy())
		self.redo_history = []
		self.window.update_history_sensitivity()
		self.window.drawing_area.queue_draw()
		self.set_pixbuf_as_stable()
		self.selection_is_active = False
		self.update_selection_actions()
		self.update_minimap()

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

	def update_minimap(self):
		w = self.preview_size
		h = self.preview_size
		if self.main_pixbuf.get_height() > self.main_pixbuf.get_width(): # TODO comparer la taille de full_pixbuf plutôt
			w = self.preview_size * (self.main_pixbuf.get_width()/self.main_pixbuf.get_height())
		else:
			h = self.preview_size * (self.main_pixbuf.get_height()/self.main_pixbuf.get_width())
		self.mini_pixbuf = self.main_pixbuf.scale_simple(w, h, GdkPixbuf.InterpType.TILES) # full_pixbuf
		self.mini_surface = Gdk.cairo_surface_create_from_pixbuf(self.mini_pixbuf, 0, None)
		self.window.minimap_area.set_size(self.mini_surface.get_width(), self.mini_surface.get_height())
		self.window.minimap_area.set_size_request(self.mini_surface.get_width(), self.mini_surface.get_height())
		self.window.minimap_area.queue_draw()

	def use_stable_pixbuf(self):
		self.surface = Gdk.cairo_surface_create_from_pixbuf(self.main_pixbuf, 0, None)

	def undo_operation(self):
		self.redo_history.append(self.main_pixbuf.copy())
		self.main_pixbuf = self.undo_history.pop()
		self.use_stable_pixbuf()
		self.update_minimap()

	def redo_operation(self):
		self.undo_history.append(self.main_pixbuf.copy())
		self.main_pixbuf = self.redo_history.pop()
		self.use_stable_pixbuf()
		self.update_minimap()

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

	def create_selection_from_main(self, x0, y0, x1, y1):
		w = int(x1 - x0)
		h = int(y1 - y0)
		if w <= 0 or h <= 0:
			return
		self.selection_x = int(x0)
		self.selection_y = int(y0)
		temp_surface = Gdk.cairo_surface_create_from_pixbuf(self.main_pixbuf, 0, None)
		temp_surface = temp_surface.map_to_image(cairo.RectangleInt(int(x0), int(y0), w, h))
		self.selection_pixbuf = Gdk.pixbuf_get_from_surface(temp_surface, 0, 0, \
			temp_surface.get_width(), temp_surface.get_height())
		self.set_temp()

	def create_selection_from_selection(self):
		self.selection_is_active = True
		self.temp_pixbuf = None
		self.update_selection_actions()

	def set_temp(self):
		self.temp_x = self.selection_x
		self.temp_y = self.selection_y
		self.temp_pixbuf = self.selection_pixbuf.copy()
		self.selection_is_active = True
		self.update_selection_actions()

	def delete_temp(self):
		if self.temp_pixbuf is None:
			return
		x0 = self.temp_x
		y0 = self.temp_y
		x1 = x0 + self.temp_pixbuf.get_width()
		y1 = y0 + self.temp_pixbuf.get_height()
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

	def show_selection_rectangle(self):
		self.use_stable_pixbuf()
		if self.selection_is_active:
			self.delete_temp()
		x0 = self.selection_x
		y0 = self.selection_y
		x1 = x0 + self.selection_pixbuf.get_width()
		y1 = y0 + self.selection_pixbuf.get_height()
		self.show_selection_content()
		w_context = cairo.Context(self.surface)
		w_context.move_to(x1-1, y1-1)
		w_context.line_to(x1-1, y0+1)
		w_context.line_to(x0+1, y0+1)
		w_context.line_to(x0+1, y1-1)
		w_context.close_path()
		w_context.clip_preserve()
		w_context.set_source_rgba(0.1, 0.1, 0.3, 0.2)
		w_context.paint()
		w_context.stroke()

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
		self.set_temp()
		self.show_selection_rectangle()

	def export_selection_as(self):
		file_path = self.window.run_save_file_chooser('')
		if file_path is not None:
			self.selection_pixbuf.savev(file_path, file_path.split('.')[-1], [None], [])

	def update_selection_actions(self):
		self.window.update_selection_actions(self.selection_is_active)
