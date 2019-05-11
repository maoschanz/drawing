# tool_crop.py
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

from .abstract_canvas_tool import AbstractCanvasTool

class ToolCrop(AbstractCanvasTool):
	__gtype_name__ = 'ToolCrop'

	def __init__(self, window):
		super().__init__('crop', _("Crop"), 'tool-crop-symbolic', window)
		self.cursor_name = 'se-resize'
		self.apply_to_selection = False
		self.x_press = 0
		self.y_press = 0
		self.move_instead_of_crop = False

		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/drawing/tools/ui/tool_crop.ui')
		self.bottom_panel = builder.get_object('bottom-panel')
		self.centered_box = builder.get_object('centered_box')
		self.cancel_btn = builder.get_object('cancel_btn')
		self.apply_btn = builder.get_object('apply_btn')

		self.height_btn = builder.get_object('height_btn')
		self.width_btn = builder.get_object('width_btn')
		# FIXME X et Y ? TODO

		self.window.bottom_panel_box.add(self.bottom_panel)

	def get_edition_status(self):
		if self.apply_to_selection:
			return _("Cropping the selection")
		else:
			return _("Cropping the canvas")

###################################################

	def on_tool_selected(self, *args):
		self.apply_to_selection = (self.window.hijacker_id is not None)
		self._x = 0
		self._y = 0
		if self.apply_to_selection:
			self.init_if_selection()
		else:
			self.init_if_main()
		self.width_btn.connect('value-changed', self.on_width_changed)
		self.height_btn.connect('value-changed', self.on_height_changed)
		self.width_btn.set_value(self.original_width)
		self.height_btn.set_value(self.original_height)

	def init_if_selection(self):
		self.original_width = self.get_image().selection_pixbuf.get_width()
		self.original_height = self.get_image().selection_pixbuf.get_height()
		self.width_btn.set_range(1, self.original_width)
		self.height_btn.set_range(1, self.original_height)

	def init_if_main(self):
		self.original_width = self.get_image().get_pixbuf_width()
		self.original_height = self.get_image().get_pixbuf_height()
		self.width_btn.set_range(1, 10*self.original_width)
		self.height_btn.set_range(1, 10*self.original_height)

	def crop_temp_pixbuf(self, x, y, width, height):
		x = max(x, 0)
		y = max(y, 0)
		min_w = min(width, self.get_image().get_temp_pixbuf().get_width() - x)
		min_h = min(height, self.get_image().get_temp_pixbuf().get_height() - y)
		new_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, width, height)
		new_pixbuf.fill(0)
		self.get_image().temp_pixbuf.copy_area(x, y, min_w, min_h, new_pixbuf, 0, 0)
		self.get_image().temp_pixbuf = new_pixbuf

	def scale_temp_pixbuf_to_area(self, width, height):
		visible_w = self.get_image().get_allocated_width()
		visible_h = self.get_image().get_allocated_height()
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
		pb = self.get_image().get_temp_pixbuf()
		self.get_image().set_temp_pixbuf(pb.scale_simple(nice_w, nice_h, GdkPixbuf.InterpType.TILES))

	def get_width(self):
		return self.width_btn.get_value_as_int()

	def get_height(self):
		return self.height_btn.get_value_as_int()

	def on_width_changed(self, *args):
		self.update_temp_pixbuf()

	def on_height_changed(self, *args):
		self.update_temp_pixbuf()

	def on_motion_on_area(self, area, event, surface, event_x, event_y):
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
		self.update_temp_pixbuf()

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color, event_x, event_y):
		self.x_press = event.x
		self.y_press = event.y
		self.move_instead_of_crop = (event.button == 3)

	def validate_coords(self):
		self._x = max(self._x, 0)
		self._y = max(self._y, 0)
		max_w = self.get_image().get_temp_pixbuf().get_width() - self.get_width()
		max_h = self.get_image().get_temp_pixbuf().get_height() - self.get_height()
		self._x = min(self._x, max_w)
		self._y = min(self._y, max_h)
		x = int(self._x)
		y = int(self._y)
		width = self.get_width()
		height = self.get_height()
		return x, y, width, height

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'is_selection': self.apply_to_selection,
			'is_preview': True,
			'x': self._x,
			'y': self._y,
			'width': self.get_width(),
			'height': self.get_height()
		}
		return operation

	def do_tool_operation(self, operation):
		if operation['tool_id'] != self.id:
			return
		self.restore_pixbuf()
		x = operation['x']
		y = operation['y']
		width = operation['width']
		height = operation['height']
		if operation['is_selection']:
			source_pixbuf = self.get_selection_pixbuf()
		else:
			source_pixbuf = self.get_main_pixbuf()
		self.get_image().set_temp_pixbuf(source_pixbuf.copy())
		x, y, width, height = self.validate_coords()
		self.crop_temp_pixbuf(x, y, width, height)

		if not operation['is_selection'] and operation['is_preview']:
			self.scale_temp_pixbuf_to_area(width, height)

		if operation['is_preview']:
			self.finish_pixbuf_tool_operation_preview(operation['is_selection'])
		else:
			self.get_image().main_pixbuf = self.get_image().get_temp_pixbuf().copy()
			self.restore_pixbuf()


