# minimap.py
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

from gi.repository import Gtk, Gdk, GdkPixbuf
import cairo

from .utilities import utilities_show_overlay_on_context

class DrawingMinimap(Gtk.Popover):
	__gtype_name__ = 'DrawingMinimap'
	# TODO custom "move" cursor

	def __init__(self, window, minimap_btn, **kwargs):
		super().__init__(**kwargs)
		self.window = window
		self.minimap_btn = minimap_btn
		self.preview_size = self.window._settings.get_int('preview-size')
		self.mini_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 300, 300)
		self.mini_surface = cairo.ImageSurface(cairo.Format.ARGB32, 5, 5)

		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/drawing/ui/minimap.ui')
		box = builder.get_object('minimap_box')
		# if self.window._settings.get_boolean('devel-only'): # XXX à retirer
		# 	box.show_all()

		self.zoom_scale = builder.get_object('zoom_scale')
		# self.zoom_scale.connect('', self.) # TODO

		self.minimap_area = builder.get_object('minimap_area')
		self.minimap_area.set_size(200, 200)
		self.minimap_area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | \
			Gdk.EventMask.BUTTON_RELEASE_MASK)
		self.minimap_area.connect('draw', self.on_minimap_draw)
		self.minimap_area.connect('button-press-event', self.on_minimap_press)
		self.minimap_area.connect('button-release-event', self.on_minimap_release)

		self.add(box)
		self.set_relative_to(self.minimap_btn)
		self.connect('closed', self.on_popover_dismissed)

	def update_zoom_scale(self, value):
		self.zoom_scale.set_value(value * 100)

	def on_popover_dismissed(self, *args):
		"""Callback of the 'closed' signal, updating the state of the action."""
		self.minimap_btn.set_active(False)

	def on_minimap_draw(self, area, cairo_context):
		"""Callback of the 'draw' signal, painting the area with the surface."""
		cairo_context.set_source_surface(self.mini_surface, 0, 0)
		cairo_context.paint()

	def on_minimap_press(self, area, event):
		"""Callback of the 'button-press-event' signal."""
		self.old_x = event.x
		self.old_y = event.y

	def on_minimap_release(self, area, event):
		"""Callback of the 'button-release-event' signal."""
		ratio = self.get_main_pixbuf().get_width()/self.mini_pixbuf.get_width()
		delta_x = int((event.x - self.old_x) * ratio)
		delta_y = int((event.y - self.old_y) * ratio)
		self.window.get_active_image().add_deltas(delta_x, delta_y, 1)

	def get_main_pixbuf(self):
		return self.window.get_active_image().main_pixbuf

	def update_minimap(self, *args):
		"""Update the overlay on the minimap, based on the scroll coordinates."""
		x = self.window.get_active_image().scroll_x
		y = self.window.get_active_image().scroll_y
		w = self.preview_size
		h = self.preview_size
		mpb_width = self.get_main_pixbuf().get_width()
		mpb_height = self.get_main_pixbuf().get_height()
		if mpb_height > mpb_width:
			w = self.preview_size * (mpb_width/mpb_height)
		else:
			h = self.preview_size * (mpb_height/mpb_width)
		self.mini_pixbuf = self.get_main_pixbuf().scale_simple(w, h, \
		                                             GdkPixbuf.InterpType.TILES)
		self.mini_surface = Gdk.cairo_surface_create_from_pixbuf(self.mini_pixbuf, 0, None)
		self.minimap_area.set_size_request(self.mini_surface.get_width(), \
		                                         self.mini_surface.get_height())

		visible_width = min(self.window.get_active_image().get_allocated_width(), \
		                    mpb_width - x)
		visible_height = min(self.window.get_active_image().get_allocated_height(), \
		                     mpb_height - y)
		if self.window.get_active_image().get_allocated_width() < mpb_width \
		or self.window.get_active_image().get_allocated_height() < mpb_height:
			mini_x = x * self.mini_pixbuf.get_width()/mpb_width
			mini_y = y * self.mini_pixbuf.get_height()/mpb_height
			mini_width = visible_width * self.mini_pixbuf.get_width()/mpb_width
			mini_height = visible_height * self.mini_pixbuf.get_height()/mpb_height
			mini_context = cairo.Context(self.mini_surface)
			mini_context.move_to(mini_x, mini_y)
			mini_context.line_to(mini_x, mini_height + mini_y)
			mini_context.line_to(mini_width + mini_x, mini_height + mini_y)
			mini_context.line_to(mini_width + mini_x, mini_y)
			mini_context.close_path()
			mini_path = mini_context.copy_path()
			utilities_show_overlay_on_context(mini_context, mini_path, False)
		# else:
		# 	???
		self.minimap_area.queue_draw()
		self.update_main_area()

	def update_main_area(self):
		self.window.get_active_image().update()
