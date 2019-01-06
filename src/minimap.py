# minimap.py
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

from gi.repository import Gtk, Gdk, GdkPixbuf
import cairo

class DrawingMinimap(Gtk.Popover):
	__gtype_name__ = 'DrawingMinimap'

	def __init__(self, window, minimap_btn, **kwargs):
		super().__init__(**kwargs)
		self.window = window
		self.preview_size = self.window._settings.get_int('preview-size')
		self.preview_x = 0
		self.preview_y = 0
		self.mini_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 300, 300) # 8 ??? les autres plantent
		self.mini_surface = cairo.ImageSurface(cairo.Format.ARGB32, 5, 5)

		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/Drawing/ui/minimap.ui')
		box = builder.get_object('minimap_box')

		self.minimap_area = builder.get_object('minimap_area')
		self.minimap_area.set_size(200, 200)
		self.minimap_area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | \
			Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.POINTER_MOTION_MASK)
		self.minimap_area.connect('draw', self.on_minimap_draw)
		# self.minimap_area.connect('motion-notify-event', self.on_minimap_motion)
		self.minimap_area.connect('button-press-event', self.on_minimap_press)
		self.minimap_area.connect('button-release-event', self.on_minimap_release)

		self.add(box)
		minimap_btn.set_popover(self)
		minimap_btn.connect('toggled', self.update_minimap)

	def action_smaller_preview(self, *args):
		size = max(200, self.window._settings.get_int('preview-size') - 40)
		self.window._settings.set_int('preview-size', size)
		self.preview_size = size
		self.update_minimap()

	def action_bigger_preview(self, *args):
		size = self.window._settings.get_int('preview-size') + 40
		self.window._settings.set_int('preview-size', size)
		self.preview_size = size
		self.update_minimap()

	def on_minimap_draw(self, area, cairo_context):
		cairo_context.set_source_surface(self.mini_surface, 0, 0)
		cairo_context.paint()

	def on_minimap_press(self, area, event):
		self.old_x = event.x
		self.old_y = event.y

	def on_minimap_release(self, area, event):
		delta_x = event.x - self.old_x
		delta_y = event.y - self.old_y
		mpb_width = self.get_main_pixbuf().get_width()
		mpb_height = self.get_main_pixbuf().get_height()
		delta_x = delta_x * mpb_width/self.mini_pixbuf.get_width()
		delta_y = delta_y * mpb_height/self.mini_pixbuf.get_height()
		self.preview_x = int(self.preview_x + delta_x)
		self.preview_y = int(self.preview_y + delta_y)
		if self.preview_x < 0:
			self.preview_x = 0
		if self.preview_y < 0:
			self.preview_y = 0
		if self.preview_x + self.window.drawing_area.get_allocated_width() > mpb_width:
			self.preview_x = mpb_width - self.window.drawing_area.get_allocated_width()
		if self.preview_y + self.window.drawing_area.get_allocated_height() > mpb_height:
			self.preview_y = mpb_height - self.window.drawing_area.get_allocated_height()
		self.update_minimap()

	def get_main_pixbuf(self):
		return self.window.main_pixbuf

	def update_minimap(self, *args):
		w = self.preview_size
		h = self.preview_size
		mpb_width = self.get_main_pixbuf().get_width()
		mpb_height = self.get_main_pixbuf().get_height()
		if mpb_height > mpb_width:
			w = self.preview_size * (mpb_width/mpb_height)
		else:
			h = self.preview_size * (mpb_height/mpb_width)
		self.mini_pixbuf = self.get_main_pixbuf().scale_simple(w, h, GdkPixbuf.InterpType.TILES)
		self.mini_surface = Gdk.cairo_surface_create_from_pixbuf(self.mini_pixbuf, 0, None)
		self.minimap_area.set_size_request(self.mini_surface.get_width(), self.mini_surface.get_height())

		visible_width = min(self.window.drawing_area.get_allocated_width(), \
			mpb_width - self.preview_x)
		visible_height = min(self.window.drawing_area.get_allocated_height(), \
			mpb_height - self.preview_y)
		if self.window.drawing_area.get_allocated_width() < mpb_width \
		or self.window.drawing_area.get_allocated_height() < mpb_height:
			mini_x = self.preview_x * self.mini_pixbuf.get_width()/mpb_width
			mini_y = self.preview_y * self.mini_pixbuf.get_height()/mpb_height
			mini_width = visible_width * self.mini_pixbuf.get_width()/mpb_width
			mini_height = visible_height * self.mini_pixbuf.get_height()/mpb_height
			mini_context = cairo.Context(self.mini_surface)
			mini_context.move_to(mini_x, mini_y)
			mini_context.line_to(mini_x, mini_height + mini_y)
			mini_context.line_to(mini_width + mini_x, mini_height + mini_y)
			mini_context.line_to(mini_width + mini_x, mini_y)
			mini_context.close_path()
			mini_path = mini_context.copy_path()
			self.window.show_overlay_on_surface(self.mini_surface, mini_path)
		else:
			print('todo : ignorer explicitement preview_x et preview_y ?')
		self.minimap_area.queue_draw()

