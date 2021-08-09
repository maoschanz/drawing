# tool_scale.py
#
# Copyright 2018-2021 Romain F. T.
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

from gi.repository import Gtk, GdkPixbuf
from .abstract_transform_tool import AbstractCanvasTool
from .optionsbar_scale import OptionsBarScale
from .utilities_overlay import utilities_show_handles_on_context

class ToolScale(AbstractCanvasTool):
	__gtype_name__ = 'ToolScale'

	def __init__(self, window):
		super().__init__('scale', _("Scale"), 'tool-scale-symbolic', window)
		self.cursor_name = 'not-allowed'
		self.keep_proportions = True
		self.directions = ''
		self._x = 0
		self._y = 0
		self._x2 = 0
		self._y2 = 0
		self.x_press = 0
		self.y_press = 0
		self.add_tool_action_enum('scale-proportions', 'corners')
		# self.add_tool_action_enum('scale-unit', 'pixels') # TODO

	def try_build_pane(self):
		self.pane_id = 'scale'
		self.window.options_manager.try_add_bottom_pane(self.pane_id, self)

	def build_bottom_pane(self):
		bar = OptionsBarScale(self)
		self.width_btn = bar.width_btn
		self.height_btn = bar.height_btn
		self.width_btn.connect('value-changed', self.on_width_changed)
		self.height_btn.connect('value-changed', self.on_height_changed)
		return bar

	def get_options_label(self):
		return _("Scaling options")

	def get_edition_status(self):
		if self.apply_to_selection:
			return _("Scaling the selection")
		else:
			return _("Scaling the canvas")

	############################################################################

	def on_tool_selected(self, *args):
		super().on_tool_selected()
		self._x = 0
		self._y = 0
		self.directions = ''
		if self.apply_to_selection:
			width = self.get_selection_pixbuf().get_width()
			height = self.get_selection_pixbuf().get_height()
		else:
			width = self.get_image().get_pixbuf_width()
			height = self.get_image().get_pixbuf_height()
		self.set_keep_proportions()
		self.proportion = width/height
		self.width_btn.set_value(width)
		self.height_btn.set_value(height)
		self.build_and_do_op()

	############################################################################

	def should_set_value(self, *args):
		current_prop = self.get_width() / self.get_height()
		return self.keep_proportions and self.proportion != current_prop

	def set_keep_proportions(self, *args):
		former_setting = self.keep_proportions
		setting = self.get_option_value('scale-proportions')
		if setting == 'corners':
			self.keep_proportions = len(self.directions) != 1
		else:
			self.keep_proportions = setting == 'always'
		if self.keep_proportions == former_setting:
			return
		if self.keep_proportions:
			self.proportion = self.get_width() / self.get_height()

	############################################################################

	def on_width_changed(self, *args):
		if self.directions == '':
			# Means we use the spinbtn directly, instead of the surface signals
			self.set_keep_proportions()
		if self.should_set_value():
			self.height_btn.set_value(self.get_width() / self.proportion)
		self.build_and_do_op()

	def on_height_changed(self, *args):
		if self.directions == '':
			# Means we use the spinbtn directly, instead of the surface signals
			self.set_keep_proportions()
		if self.should_set_value():
			self.width_btn.set_value(self.get_height() * self.proportion)
		else:
			self.build_and_do_op()

	def get_width(self):
		return self.width_btn.get_value_as_int()

	def get_height(self):
		return self.height_btn.get_value_as_int()

	############################################################################

	def on_unclicked_motion_on_area(self, event, surface):
		self.cursor_name = self.get_handle_cursor_name(event.x, event.y)
		self.window.set_cursor(True)

	def on_press_on_area(self, event, surface, event_x, event_y):
		self.x_press = event_x
		self.y_press = event_y
		self._x2 = self._x + self.get_width()
		self._y2 = self._y + self.get_height()
		self.directions = self.cursor_name.replace('-resize', '')
		self.set_keep_proportions()

	def on_motion_on_area(self, event, surface, event_x, event_y, render=True):
		if self.cursor_name == 'not-allowed':
			return
		delta_x = event_x - self.x_press
		delta_y = event_y - self.y_press
		self.x_press = event_x
		self.y_press = event_y

		height = self.get_height()
		width = self.get_width()
		if 'n' in self.directions:
			height -= delta_y
			self._y = self._y + delta_y
		if 's' in self.directions:
			height += delta_y
		if 'w' in self.directions:
			width -= delta_x
			self._x = self._x + delta_x
		if 'e' in self.directions:
			width += delta_x

		if self.apply_to_selection and self.keep_proportions:
			if 'w' in self.directions:
				self._x = self._x2 - width
			if 'n' in self.directions:
				self._y = self._y2 - height

		if self.keep_proportions:
			if abs(delta_y) > abs(delta_x):
				self.height_btn.set_value(height)
			else:
				self.width_btn.set_value(width)
		else:
			self.height_btn.set_value(height)
			self.width_btn.set_value(width)

	def on_release_on_area(self, event, surface, event_x, event_y):
		self.on_motion_on_area(event, surface, event_x, event_y)
		self.directions = ''
		self.build_and_do_op() # technically already done

	############################################################################

	def on_draw_above(self, area, cairo_context):
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
		self._draw_temp_pixbuf(cairo_context, x1, y1)
		thickness = self.get_overlay_thickness()
		utilities_show_handles_on_context(cairo_context, x1, x2, y1, y2, thickness)

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
		self.start_tool_operation(operation)
		if operation['is_selection']:
			source_pixbuf = self.get_selection_pixbuf()
		else:
			source_pixbuf = self.get_main_pixbuf()
		self.get_image().set_temp_pixbuf(source_pixbuf.scale_simple( \
		                                 operation['width'], \
		                                 operation['height'], \
		                                 GdkPixbuf.InterpType.TILES))
		self.common_end_operation(operation)

	############################################################################
################################################################################

