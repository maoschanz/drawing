# image.py
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
import cairo, os

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
		self.init_instance_attributes()

		self.add_events( \
			Gdk.EventMask.BUTTON_PRESS_MASK | \
			Gdk.EventMask.BUTTON_RELEASE_MASK | \
			Gdk.EventMask.BUTTON_MOTION_MASK | \
			Gdk.EventMask.SMOOTH_SCROLL_MASK)

		self.update_history_sensitivity()

		self.handlers.append( self.connect('draw', self.on_draw) )
		self.handlers.append( self.connect('motion-notify-event', self.on_motion_on_area) )
		self.handlers.append( self.connect('button-press-event', self.on_press_on_area) )
		self.handlers.append( self.connect('button-release-event', self.on_release_on_area) )
		self.handlers.append( self.connect('scroll-event', self.on_scroll_on_area) )

		self.init_background()

	def init_instance_attributes(self):
		self.handlers = []
		self.scroll_x = 0
		self.scroll_y = 0
		self.selection_x = 1
		self.selection_y = 1
		self.selection_path = None
		self.is_clicked = False
		self.undo_history = []
		self.redo_history = []
		self.gfile = None
		self.filename = None
		self._is_saved = True

		width = self.window._settings.get_int('default-width')
		height = self.window._settings.get_int('default-height')

		# 8 ??? les autres plantent
		self.main_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, width, height)
		self.temp_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 1, 1)
		self.selection_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 1, 1)

		self.surface = cairo.ImageSurface(cairo.Format.ARGB32, width, height)

	def init_background(self, *args): # pourquoi ce blanc ? XXX FIXME
		w_context = cairo.Context(self.surface)
		r = float(self.window._settings.get_strv('default-rgba')[0])
		g = float(self.window._settings.get_strv('default-rgba')[1])
		b = float(self.window._settings.get_strv('default-rgba')[2])
		a = float(self.window._settings.get_strv('default-rgba')[3])
		w_context.set_source_rgba(r, g, b, a)
		w_context.paint()
		# TODO opération
		self.queue_draw()
		self.set_surface_as_stable_pixbuf()

	def initial_save(self):
		self.window.set_picture_title()
		self._is_saved = True
		self.use_stable_pixbuf()
		self.queue_draw()

	# FILE MANAGEMENT

	def edit_properties(self):
		DrawingPropertiesDialog(self.window, self)

	def get_file_path(self):
		if self.gfile is None:
			return None
		else:
			return self.gfile.get_path()

	def try_load_file(self):
		if self.get_file_path() is None:
			return
		else:
			self.main_pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.get_file_path())
			self.initial_save()

	# HISTORY MANAGEMENT

	def try_undo(self, *args):
		should_undo = not self.active_tool().give_back_control()
		if should_undo and self.can_undo():
			self.redo_history.append(self.main_pixbuf.copy())
			self.main_pixbuf = self.undo_history.pop()
			self.use_stable_pixbuf()
			self.update_history_sensitivity()
		self.queue_draw()

	def try_redo(self, *args):
		self.undo_history.append(self.main_pixbuf.copy())
		self.main_pixbuf = self.redo_history.pop()
		self.use_stable_pixbuf()
		self.queue_draw()
		self.update_history_sensitivity()

	def update_history_sensitivity(self):
		#self.window.lookup_action('undo').set_enabled(self.can_undo())
		#self.window.lookup_action('redo').set_enabled(len(self.redo_history) != 0)
		self.window.lookup_action('undo').set_enabled(False)
		self.window.lookup_action('redo').set_enabled(False)

	def add_operation_to_history(self, operation):
		print('todo')

	def on_tool_finished(self):
		#self.undo_history.append(self.main_pixbuf.copy())
		#self.redo_history = []
		#self.update_history_sensitivity()
		self.queue_draw()
		self.set_surface_as_stable_pixbuf()
		self.active_tool().update_actions_state()

	def can_undo(self):
		return True # FIXME prendre en compte la possibilité de cancel une opération en cours ??
		if len(self.undo_history) == 0:
			return False
		else:
			return True

	# DRAWING OPERATIONS

	def on_draw(self, area, cairo_context):
		cairo_context.set_source_surface(self.get_surface(), \
			-1*self.scroll_x, -1*self.scroll_y)
		cairo_context.paint()

		if self.is_using_selection() and self.selection_pixbuf is not None:
			utilities_show_overlay_on_context(cairo_context, self.get_selection_path(), True)

	def delete_former_selection(self):
		self.window.tools['select'].delete_temp() # XXX beurk

	def on_press_on_area(self, area, event): # XXX
		if event.button == 2:
			self.is_clicked = False
			self.window.action_exchange_color()
			return
		self.is_clicked = True
		self._is_saved = False
		x, y = self.get_main_coord()
		self.active_tool().on_press_on_area(area, event, self.surface, \
			self.window.size_setter.get_value(), \
			self.get_left_rgba(), self.get_right_rgba(), \
			x + event.x, y + event.y)

	def on_motion_on_area(self, area, event): # FIXME
		if not self.is_clicked:
			return
		x, y = self.get_main_coord()
		event_x = x + event.x
		event_y = y + event.y
		self.active_tool().on_motion_on_area(area, event, self.surface, event_x, event_y)
		self.queue_draw()

	def on_release_on_area(self, area, event): # FIXME
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

	def on_scroll_on_area(self, area, event): # FIXME
		self.add_deltas(event.delta_x, event.delta_y, 10)

	def get_main_coord(self, *args): # FIXME
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

	def get_selection_path(self):
		#return self.selection_path
		return self.active_tool().get_dragged_selection_path() # XXX je sais meme pas pourquoi ça marche
		# FIXME en fait ça marche bien mal lol

	def get_selection_pixbuf(self):
		return self.selection_pixbuf

	def set_selection_pixbuf(self, new_pixbuf):
		if new_pixbuf is None:
			return False
		else:
			self.selection_pixbuf = new_pixbuf
			return True

########################

	def get_surface(self):
		return self.surface

	def set_surface_as_stable_pixbuf(self):
		self.main_pixbuf = Gdk.pixbuf_get_from_surface(self.surface, 0, 0, \
			self.surface.get_width(), self.surface.get_height())

	def use_stable_pixbuf(self):
		self.surface = Gdk.cairo_surface_create_from_pixbuf(self.main_pixbuf, 0, None)

	def is_using_temp(self):
		return self.window.tool_needs_temp()

	def is_using_selection(self):
		return self.window.tool_needs_selection()

	def add_operation_to_history(self, operation):
		print('todo')

##########################

	def image_select_all(self):
		self.selection_x = 0
		self.selection_y = 0
		self.set_selection_pixbuf(self.get_main_pixbuf().copy())

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
