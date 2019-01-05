# pixbuf_manager.py

from gi.repository import Gtk, Gdk, Gio, GdkPixbuf, GLib
import cairo

class DrawingPixbufManager():

	def __init__(self, window):
		self.window = window

		width = self.window._settings.get_int('default-width')
		height = self.window._settings.get_int('default-height')

		self.gfile = None

		# INIT PIXBUFS AND SURFACES

		# self.full_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, width, height) # 8 ??? les autres plantent
		self.main_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, width, height) # 8 ??? les autres plantent
		self.temporary_pixbuf = None # TODO

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

	def on_tool_finished(self):
		self.undo_history.append(self.main_pixbuf.copy())
		self.redo_history = []
		self.window.update_history_sensitivity()
		self.window.drawing_area.queue_draw()
		self.set_pixbuf_as_stable()
		self.window.active_tool().update_actions_state()

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

	def show_overlay_on_surface(self, surface, cairo_path): # TODO doit être utilisé dans les modes
		w_context = cairo.Context(surface)
		w_context.new_path()
		w_context.append_path(cairo_path)
		w_context.clip_preserve()
		w_context.set_source_rgba(0.1, 0.1, 0.3, 0.2)
		w_context.paint()
		w_context.set_source_rgba(0.5, 0.5, 0.5, 0.5)
		w_context.stroke()

	def show_pixbuf_content_at(self, pixbuf, x, y):
		if pixbuf is None:
			return
		w_context = cairo.Context(self.surface)
		Gdk.cairo_set_source_pixbuf(w_context, pixbuf, x, y)
		w_context.paint()

	def scale_pixbuf_to(self, new_width, new_height):
		self.main_pixbuf = self.main_pixbuf.scale_simple(new_width, new_height, GdkPixbuf.InterpType.TILES)
		self.use_stable_pixbuf()
		self.on_tool_finished()

