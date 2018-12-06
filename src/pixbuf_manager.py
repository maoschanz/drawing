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

SETTINGS_SCHEMA = 'com.github.maoschanz.Drawing'

# TODO
# gestion du pixbuf de sélection
# gestion du presse-papier
class DrawingPixbufManager():
	main_pixbuf = None
	selection_pixbuf = None
	surface = None

	undo_history = []
	redo_history = []

	def __init__(self, window):
		self.window = window
		self.settings = Gio.Settings.new(SETTINGS_SCHEMA)

		width = self.settings.get_int('default-width')
		height = self.settings.get_int('default-height')

		self.main_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, width, height) # 8 ??? les autres plantent
		# self.selection_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 1, 1) # 8 ??? les autres plantent
		self.surface = cairo.ImageSurface(cairo.Format.ARGB32, width, height)
		# self.drawing_area.set_size(1000, 600) # osef

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
			self.set_stable_pixbuf()
			self.main_pixbuf.savev(file_path, file_format, [None], [])

	def resize_surface(self, x, y, width, height):
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
			self.resize_surface(0, 0, width, height)

	def on_tool_finished(self):
		self.undo_history.append(self.main_pixbuf.copy())
		self.redo_history = []
		self.window.update_history_sensitivity()
		self.set_pixbuf_as_stable()

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

	def cut_operation(self):
		pass

	def copy_operation(self):
		pass

	def paste_operation(self):
		pass


