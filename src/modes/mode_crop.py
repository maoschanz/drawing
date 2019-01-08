# crop.py
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

from gi.repository import Gtk, Gdk, Gio, GLib, GdkPixbuf

from .modes import ModeTemplate
from .minimap import DrawingMinimap

class ModeCrop(ModeTemplate):
	__gtype_name__ = 'ModeCrop'

	def __init__(self, window):
		super().__init__(window)
		self.crop_selection = False
		self.x_press = 0
		self.y_press = 0
		self.move_instead_of_crop = False

		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/Drawing/modes/ui/mode_crop.ui')
		self.bottom_panel = builder.get_object('bottom-panel')

		self.height_btn = builder.get_object('height_btn')
		self.width_btn = builder.get_object('width_btn')

	def get_panel(self):
		return self.bottom_panel

	def get_edition_status(self):
		if self.crop_selection:
			return _("Cropping the selection")
		else:
			return _("Cropping the canvas")

	def on_mode_selected(self, *args):
		self.crop_selection = args[0]
		self._x = 0
		self._y = 0
		if self.crop_selection:
			self.original_width = self.window.active_tool().selection_pixbuf.get_width()
			self.original_height = self.window.active_tool().selection_pixbuf.get_height()
		else:
			self.original_width = self.window.get_pixbuf_width()
			self.original_height = self.window.get_pixbuf_height()
		self.width_btn.connect('value-changed', self.on_width_changed)
		self.height_btn.connect('value-changed', self.on_height_changed)

		if self.crop_selection:
			self.width_btn.set_range(1, self.original_width)
			self.height_btn.set_range(1, self.original_height)
			w = self.original_width
			h = self.original_height
		else:
			self.width_btn.set_range(1, 2*self.original_width)
			self.height_btn.set_range(1, 2*self.original_height)
			w = self.original_width
			h = self.original_height
		self.width_btn.set_value(w)
		self.height_btn.set_value(h)
		self.set_action_sensitivity('active_tool', False)

	def on_apply_mode(self):
		x = self._x
		y = self._y
		width = self.get_width()
		height = self.get_height()
		if self.crop_selection:
			self.window.active_tool().action_crop(x, y, width, height)
		else:
			self.window.crop_main_pixbuf(x, y, width, height)
			self.window.on_tool_finished()

	def on_draw(self, area, cairo_context, main_x, main_y):
		if self.crop_selection:
			self.window.temporary_pixbuf = self.window.active_tool().selection_pixbuf.copy()
			x, y, width, height = self.validate_coords()
			self.crop_temp_pixbuf(x, y, width, height)
			self.window.active_tool().delete_temp()
			selection_x = self.window.active_tool().selection_x
			selection_y = self.window.active_tool().selection_y
			self.window.show_pixbuf_content_at(self.window.temporary_pixbuf, selection_x, selection_y)
			super().on_draw(area, cairo_context, main_x, main_y)
		else:
			self.window.temporary_pixbuf = self.window.main_pixbuf.copy()
			x, y, width, height = self.validate_coords()
			self.crop_temp_pixbuf(x, y, width, height)
			self.scale_temp_pixbuf_to_area(width, height)
			Gdk.cairo_set_source_pixbuf(cairo_context, self.window.temporary_pixbuf, 0, 0)
			cairo_context.paint()

	def crop_temp_pixbuf(self, x, y, width, height):
		min_w = min(width, self.window.temporary_pixbuf.get_width() + x)
		min_h = min(height, self.window.temporary_pixbuf.get_height() + y)
		new_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, width, height)
		new_pixbuf.fill(0)
		self.window.temporary_pixbuf.copy_area(x, y, min_w, min_h, new_pixbuf, 0, 0)
		self.window.temporary_pixbuf = new_pixbuf

	def scale_temp_pixbuf_to_area(self, width, height):
		visible_w = self.window.drawing_area.get_allocated_width()
		visible_h = self.window.drawing_area.get_allocated_height()
		w_ratio = visible_w/width
		h_ratio = visible_h/height
		if w_ratio > 1.0 and h_ratio > 1.0:
			nice_w = width
			nice_h = height
		elif visible_h/visible_w > height/width:
			nice_w = visible_w
			nice_h = int(height * w_ratio)
		else:
			nice_w = int(width * h_ratio)
			nice_h = visible_h
		self.window.temporary_pixbuf = self.window.temporary_pixbuf.scale_simple(nice_w, nice_h, GdkPixbuf.InterpType.TILES)

	def get_width(self):
		return self.width_btn.get_value_as_int()

	def get_height(self):
		return self.height_btn.get_value_as_int()

	def on_width_changed(self, *args):
		self.non_destructive_show_modif()

	def on_height_changed(self, *args):
		self.non_destructive_show_modif()

	def on_motion_on_area(self, area, event, surface, event_x, event_y):
		if self.window.is_clicked:
			delta_x = event.x - self.x_press
			delta_y = event.y - self.y_press
			if self.move_instead_of_crop:
				self._x = self._x - delta_x
				self._y = self._y - delta_y
			else:
				self.width_btn.set_value(self.width_btn.get_value() + delta_x)
				self.height_btn.set_value(self.height_btn.get_value() + delta_y)
			self.x_press = event.x
			self.y_press = event.y

	def on_press_on_area(self, area, event, surface, event_x, event_y):
		self.x_press = event.x
		self.y_press = event.y
		self.move_instead_of_crop = (event.button == 3)

	def validate_coords(self):
		self._x = max(self._x, 0)
		self._y = max(self._y, 0)
		max_w = self.window.temporary_pixbuf.get_width() - self.get_width()
		max_h = self.window.temporary_pixbuf.get_height() - self.get_height()
		self._x = min(self._x, max_w)
		self._y = min(self._y, max_h)
		x = int(self._x)
		y = int(self._y)
		width = self.get_width()
		height = self.get_height()
		return x, y, width, height
