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

import cairo
from gi.repository import Gtk, Gdk, GdkPixbuf
from .utilities_tools import utilities_show_overlay_on_context

class DrawingMinimap(Gtk.Popover):
	__gtype_name__ = 'DrawingMinimap'
	# TODO custom "move" cursor
	# TODO "on_motion" method?

	def __init__(self, window, minimap_btn, **kwargs):
		super().__init__(**kwargs)
		self.window = window
		self.preview_size = self.window._settings.get_int('preview-size')
		self.mini_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 300, 300)
		self.mini_surface = cairo.ImageSurface(cairo.Format.ARGB32, 5, 5)

		builder = Gtk.Builder.new_from_resource( \
		                          '/com/github/maoschanz/drawing/ui/minimap.ui')
		box = builder.get_object('minimap_box')

		self.zoom_scale = builder.get_object('zoom_scale')
		self.zoom_scale.add_mark(100.0, Gtk.PositionType.TOP, None)
		self.zoom_scale.connect('value-changed', self.update_zoom_level)

		self.minimap_area = builder.get_object('minimap_area')
		self.minimap_area.set_size(200, 200)
		self.minimap_area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | \
		                                      Gdk.EventMask.BUTTON_RELEASE_MASK)
		self.minimap_area.connect('draw', self.on_minimap_draw)
		self.minimap_area.connect('button-press-event', self.on_minimap_press)
		self.minimap_area.connect('button-release-event', self.on_minimap_release)

		self.add(box)
		self.connect('closed', self.on_popover_dismissed)
		self.set_relative_to(minimap_btn)

	def update_zoom_level(self, *args):
		zoom_value = self.zoom_scale.get_value()
		self.window.get_active_image().zoom_level = zoom_value/100 # XXX superflu ?
		self.window.get_active_image().update() # XXX superflu ?
		self.set_zoom_label(zoom_value)

	def set_zoom_label(self, int_value):
		# This displays the zoom level, %s will be replaced with a number, while
		# %% is just the symbol '%'
		zoom_label = _("%s%%") % str(int(int_value))
		self.window.options_manager.set_minimap_label(zoom_label)
		self.update_minimap(False)

	def update_zoom_scale(self, value):
		self.zoom_scale.set_value(value * 100)

	def on_popover_dismissed(self, *args):
		"""Callback of the 'closed' signal, updating the state of the action."""
		try:
			self.get_relative_to().set_active(False)
		except:
			pass

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
		image = self.window.get_active_image()
		size_ratio = image.get_minimap_ratio(self.mini_pixbuf.get_width())
		delta_x = int((event.x - self.old_x) / size_ratio)
		delta_y = int((event.y - self.old_y) / size_ratio)
		image.add_deltas(delta_x, delta_y, 1)

	def update_minimap(self, force_update):
		"""Update the overlay on the minimap, based on the scroll coordinates."""
		if not self.get_visible() and not force_update:
			return
		image = self.window.get_active_image()
		self.mini_pixbuf = image.get_mini_pixbuf(self.preview_size)
		self.mini_surface = Gdk.cairo_surface_create_from_pixbuf( \
		                                              self.mini_pixbuf, 0, None)
		pix_width = self.mini_pixbuf.get_width()
		pix_height = self.mini_pixbuf.get_height()
		self.minimap_area.set_size_request(pix_width, pix_height)

		# TODO if possible, updating the overlay should be doable without first
		# rebuilding the pixbuf and the surface. It's not very useful however
		# since the guard clause prevent the update in most cases anyway.
		if image.get_show_overlay():
			size_ratio = image.get_minimap_ratio(pix_width)
			mini_x = int(image.scroll_x * size_ratio)
			mini_y = int(image.scroll_y * size_ratio)
			visible_width, visible_height = image.get_visible_size()
			mini_width = int(visible_width * size_ratio)
			mini_height = int(visible_height * size_ratio)
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
		image.update()

	############################################################################
################################################################################
