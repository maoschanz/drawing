# tool_crop.py
#
# Copyright 2018-2020 Romain F. T.
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

from .abstract_canvas_tool import AbstractCanvasTool
from .bottombar import DrawingAdaptativeBottomBar

from .utilities import utilities_add_unit_to_spinbtn
from .utilities_tools import utilities_show_handles_on_context

class ToolCrop(AbstractCanvasTool):
	__gtype_name__ = 'ToolCrop'

	def __init__(self, window):
		super().__init__('crop', _("Crop"), 'tool-crop-symbolic', window)
		self.cursor_name = 'not-allowed'
		self.apply_to_selection = False
		self.x_press = 0
		self.y_press = 0
		self.unclicked = True

	def try_build_panel(self):
		self.panel_id = 'crop'
		self.window.options_manager.try_add_bottom_panel(self.panel_id, self)

	def build_bottom_panel(self):
		bar = CropToolPanel(self.window)
		self.height_btn = bar.height_btn
		self.width_btn = bar.width_btn
		self.width_btn.connect('value-changed', self.on_width_changed)
		self.height_btn.connect('value-changed', self.on_height_changed)
		return bar

	def get_edition_status(self):
		if self.apply_to_selection:
			return _("Cropping the selection")
		else:
			return _("Cropping the canvas")

###################################################

	def on_tool_selected(self, *args):
		super().on_tool_selected()
		self._x = 0
		self._y = 0
		if self.apply_to_selection:
			self.init_if_selection()
		else:
			self.init_if_main()
		self.width_btn.set_value(self.original_width)
		self.height_btn.set_value(self.original_height)

	def init_if_selection(self):
		self.original_width = self.get_selection().selection_pixbuf.get_width()
		self.original_height = self.get_selection().selection_pixbuf.get_height()
		self.width_btn.set_range(1, self.original_width)
		self.height_btn.set_range(1, self.original_height)

	def init_if_main(self):
		self.original_width = self.get_image().get_pixbuf_width()
		self.original_height = self.get_image().get_pixbuf_height()
		self.width_btn.set_range(1, 10 * self.original_width)
		self.height_btn.set_range(1, 10 * self.original_height)

	############################################################################

	def get_width(self):
		return self.width_btn.get_value_as_int()

	def get_height(self):
		return self.height_btn.get_value_as_int()

	def on_width_changed(self, *args):
		if self.unclicked:
			self.build_and_do_op()

	def on_height_changed(self, *args):
		if self.unclicked:
			self.build_and_do_op()

	def move_north(self, delta):
		self.height_btn.set_value(self.height_btn.get_value() - delta)
		self._y = self._y + delta

	def move_south(self, delta):
		self.height_btn.set_value(self.height_btn.get_value() + delta)

	def move_east(self, delta):
		self.width_btn.set_value(self.width_btn.get_value() + delta)

	def move_west(self, delta):
		self.width_btn.set_value(self.width_btn.get_value() - delta)
		self._x = self._x + delta

	############################################################################

	def on_unclicked_motion_on_area(self, event, surface):
		self.cursor_name = self.get_handle_cursor_name(event.x, event.y)
		self.window.set_cursor(True)

	def on_press_on_area(self, event, surface, event_x, event_y):
		self.x_press = event.x
		self.y_press = event.y
		self.unclicked = False

	def on_motion_on_area(self, event, surface, event_x, event_y):
		delta_x = event.x - self.x_press
		delta_y = event.y - self.y_press

		if self.cursor_name == 'not-allowed':
			return
		else:
			directions = self.cursor_name.replace('-resize', '')
		if 'n' in directions:
			self.move_north(delta_y)
		if 's' in directions:
			self.move_south(delta_y)
		if 'w' in directions:
			self.move_west(delta_x)
		if 'e' in directions:
			self.move_east(delta_x)

		if self.apply_to_selection:
			self._x = max(0, self._x)
			self._y = max(0, self._y)

		self.x_press = event.x
		self.y_press = event.y
		# self.build_and_do_op() # better UX but slower to compute
		if not self.apply_to_selection:
			self.build_and_do_op()

	def on_release_on_area(self, event, surface, event_x, event_y):
		self.unclicked = True
		self.build_and_do_op()
		self.window.set_cursor(False)

	############################################################################

	def on_draw(self, area, cairo_context):
		if self.apply_to_selection:
			x1 = int(self._x)
			y1 = int(self._y)
		else:
			x1 = 0
			y1 = 0
		x2 = x1 + self.get_width()
		y2 = y1 + self.get_height()
		x1, x2, y1, y2 = self.get_image().get_corrected_coords(x1, x2, y1, y2, \
		                                         self.apply_to_selection, False)
		utilities_show_handles_on_context(cairo_context, x1, x2, y1, y2)
		# FIXME bien excepté les delta locaux : quand on rogne depuis le haut ou
		# la gauche, les coordonées de référence des poignées ne sont plus
		# correctes.

	############################################################################

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'is_selection': self.apply_to_selection,
			'is_preview': True,
			'local_dx': int(self._x),
			'local_dy': int(self._y),
			'width': self.get_width(),
			'height': self.get_height()
		}
		return operation

	def do_tool_operation(self, operation):
		super().do_tool_operation(operation)
		x = operation['local_dx']
		y = operation['local_dy']
		width = operation['width']
		height = operation['height']
		if operation['is_selection']:
			source_pixbuf = self.get_selection_pixbuf()
		else:
			source_pixbuf = self.get_main_pixbuf()
		self.get_image().set_temp_pixbuf(source_pixbuf.copy())
		self.crop_temp_pixbuf(x, y, width, height, operation['is_selection'])
		self.common_end_operation(operation)

	def crop_temp_pixbuf(self, x, y, width, height, is_selection):
		new_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, width, height)
		new_pixbuf.fill(0)
		src_x = max(x, 0)
		src_y = max(y, 0)
		if is_selection:
			dest_x = 0
			dest_y = 0
		else:
			dest_x = max(-1 * x, 0)
			dest_y = max(-1 * y, 0)
		temp_p = self.get_image().get_temp_pixbuf()
		min_w = min(width, temp_p.get_width() - src_x)
		min_h = min(height, temp_p.get_height() - src_y)
		temp_p.copy_area(src_x, src_y, min_w, min_h, new_pixbuf, dest_x, dest_y)
		self.get_image().temp_pixbuf = new_pixbuf

	############################################################################
################################################################################

class CropToolPanel(DrawingAdaptativeBottomBar):
	__gtype_name__ = 'CropToolPanel'

	def __init__(self, window):
		super().__init__()
		self.window = window
		builder = self.build_ui('tools/ui/tool_crop.ui')
		self.height_btn = builder.get_object('height_btn')
		self.width_btn = builder.get_object('width_btn')
		utilities_add_unit_to_spinbtn(self.height_btn, 4, 'px')
		utilities_add_unit_to_spinbtn(self.width_btn, 4, 'px')
		# XXX top/bottom/left/right ?

		self.options_btn = builder.get_object('options_btn')

		self.width_label = builder.get_object('width_label')
		self.height_label = builder.get_object('height_label')
		self.separator = builder.get_object('separator')

	def init_adaptability(self):
		super().init_adaptability()
		temp_limit_size = self.centered_box.get_preferred_width()[0] + \
		                    self.cancel_btn.get_preferred_width()[0] + \
		                   self.options_btn.get_preferred_width()[0] + \
		                     self.apply_btn.get_preferred_width()[0]
		self.set_limit_size(temp_limit_size)

	def set_compact(self, state):
		super().set_compact(state)
		if state:
			self.centered_box.set_orientation(Gtk.Orientation.VERTICAL)
		else:
			self.centered_box.set_orientation(Gtk.Orientation.HORIZONTAL)
		self.width_label.set_visible(not state)
		self.height_label.set_visible(not state)
		self.separator.set_visible(not state)

		# if self.crop_tool.apply_to_selection:
		# 	self.???.set_visible(state)
		# else:
		# 	self.???.set_visible(state)

	############################################################################
################################################################################

