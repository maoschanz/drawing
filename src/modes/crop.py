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

from gi.repository import Gtk, Gdk, Gio, GLib

from .modes import ModeTemplate
from .minimap import DrawingMinimap

class ModeCrop(ModeTemplate):
	__gtype_name__ = 'ModeCrop'

	def __init__(self, window):
		super().__init__(window)
		self.crop_selection = False

		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/Drawing/modes/ui/crop.ui')
		self.bottom_panel = builder.get_object('bottom-panel')

		self.height_btn = builder.get_object('height_btn')
		self.width_btn = builder.get_object('width_btn')

		self.minimap_btn = builder.get_object('minimap_btn')
		self.minimap_icon = builder.get_object('minimap_icon')
		self.minimap_label = builder.get_object('minimap_label')
		self.minimap = DrawingMinimap(self.window, self.minimap_btn)

	def get_panel(self):
		return self.bottom_panel

	def get_edition_status(self):
		if self.crop_selection:
			return _("Cropping the selection")
		else:
			return _("Cropping the canvas")

	def on_mode_selected(self, *args):
		self.crop_selection = args[0]
		self.forbid_growth = args[0] or args[1]
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
		elif self.forbid_growth:
			self.width_btn.set_range(1, self.original_width)
			self.height_btn.set_range(1, self.original_height)
			w = self.window.drawing_area.get_allocated_width()
			h = self.window.drawing_area.get_allocated_height()
		else:
			w = self.original_width
			h = self.original_height
		self.width_btn.set_value(w)
		self.height_btn.set_value(h)

	def adapt_to_window_size(self): # TODO
		self.minimap_label.set_visible(True)
		self.minimap_icon.set_visible(False)

	def on_apply_mode(self):
		x = self._x
		y = self._y
		width = self.get_width()
		height = self.get_height()
		if self.crop_selection:
			self.window.active_tool().crop_selection_surface(x, y, width, height)
			self.window.active_tool().selection_x += x
			self.window.active_tool().selection_y += y
			self.window.active_tool().show_selection_rectangle()
		else:
			self.window.crop_main_surface(x, y, width, height)
			self.window.on_tool_finished()

	def on_cancel_mode(self):
		print('cancel') # TODO

	def get_width(self):
		return self.width_btn.get_value_as_int()

	def get_height(self):
		return self.height_btn.get_value_as_int()

	def on_width_changed(self, *args):
		if self.forbid_growth:
			self.check_coord()
		self.draw_overlay()

	def on_height_changed(self, *args):
		if self.forbid_growth:
			self.check_coord()
		self.draw_overlay()

	def check_coord(self):
		if self._x < 0:
			self._x = 0
		elif self._x > self.original_width - self.get_width():
			self._x = self.original_width - self.get_width()
		if self._y < 0:
			self._y = 0
		elif self._y > self.original_height - self.get_height():
			self._y = self.original_height - self.get_height()

	def draw_overlay(self):
		print('todo (dynamic preview of the cropping)')
