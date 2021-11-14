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
		self._preserve_ratio = True
		self._ratio_is_inverted = False
		self._spinbtns_disabled = True
		self._directions = ''
		self._x = 0
		self._y = 0
		self._x2 = 0
		self._y2 = 0
		self.x_press = 0
		self.y_press = 0
		self.add_tool_action_enum('scale-proportions', 'corners')
		self.add_tool_action_enum('scale-unit', 'pixels')

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
		self._directions = ''
		if self.apply_to_selection:
			width = self.get_selection_pixbuf().get_width()
			height = self.get_selection_pixbuf().get_height()
		else:
			width = self.get_image().get_pixbuf_width()
			height = self.get_image().get_pixbuf_height()
		self.set_preserve_ratio()
		self._ratio = width / height
		self._spinbtns_disabled = False
		self.width_btn.set_value(width)
		self.height_btn.set_value(height)
		self.build_and_do_op()

	############################################################################

	def set_preserve_ratio(self, *args):
		"""Set whether or not `self._preserve_ratio` should be true. If it is,
		and that wasn't the case before, it sets the `self._ratio` value too."""
		former_setting = self._preserve_ratio
		setting = self.get_option_value('scale-proportions')
		if setting == 'corners':
			self._preserve_ratio = len(self._directions) != 1
		else:
			self._preserve_ratio = setting == 'always'
		if self._ratio_is_inverted:
			self._preserve_ratio = not self._preserve_ratio
		if self._preserve_ratio == former_setting:
			return
		if self._preserve_ratio:
			self._ratio = self._get_width() / self._get_height()

	def _try_scale_dimensions(self, data_dict={}):
		"""When the value in a spinbutton changes, adjust the values in the
		spinbuttons if necessary, and build-and-do the corresponding tool
		operation."""
		if not self._preserve_ratio:
			# Guard clause: if the ratio isn't locked, the dimension should be
			# applied without any change. Calculations are only useful when
			# trying to preserve the image proportions.
			self.build_and_do_op()
			return

		pixbuf = self.get_image().temp_pixbuf
		existing_width = pixbuf.get_width()
		existing_height = pixbuf.get_height()

		new_width = self._get_width()
		new_height = self._get_height()
		self._spinbtns_disabled = True

		if existing_width != new_width:
			new_height = new_width / self._ratio
			self.height_btn.set_value(new_height)
		if existing_height != new_height:
			new_width = new_height * self._ratio
			self.width_btn.set_value(new_width)

		self._spinbtns_disabled = False
		self.build_and_do_op()

	############################################################################

	def on_width_changed(self, *args):
		if self._spinbtns_disabled:
			return
		if self._directions == '':
			# Means we use the spinbtn directly, instead of the surface signals
			self.set_preserve_ratio()
		self._try_scale_dimensions()

	def on_height_changed(self, *args):
		if self._spinbtns_disabled:
			return
		if self._directions == '':
			# Means we use the spinbtn directly, instead of the surface signals
			self.set_preserve_ratio()
		self._try_scale_dimensions()

	def _get_width(self):
		return self.width_btn.get_value_as_int()

	def _get_height(self):
		return self.height_btn.get_value_as_int()

	############################################################################

	def on_unclicked_motion_on_area(self, event, surface):
		self.set_directional_cursor(event.x, event.y)

	def on_press_on_area(self, event, surface, event_x, event_y):
		self.update_modifier_state(event.state)
		if 'SHIFT' in self._modifier_keys:
			# The value will be restored later in `on_release_on_area`
			self._ratio_is_inverted = True

		self.x_press = event_x
		self.y_press = event_y
		self._x2 = self._x + self._get_width()
		self._y2 = self._y + self._get_height()
		self.set_preserve_ratio()

	def on_motion_on_area(self, event, surface, event_x, event_y, render=True):
		if self._directions == '':
			return
		delta_x = event_x - self.x_press
		delta_y = event_y - self.y_press
		self.x_press = event_x
		self.y_press = event_y

		height = self._get_height()
		width = self._get_width()
		if 'n' in self._directions:
			height -= delta_y
			self._y = self._y + delta_y
		if 's' in self._directions:
			height += delta_y
		if 'w' in self._directions:
			width -= delta_x
			self._x = self._x + delta_x
		if 'e' in self._directions:
			width += delta_x

		if self.apply_to_selection and self._preserve_ratio:
			if 'w' in self._directions:
				self._x = self._x2 - width
			if 'n' in self._directions:
				self._y = self._y2 - height

		if self._preserve_ratio:
			if abs(delta_y) > abs(delta_x):
				self.height_btn.set_value(height)
			else:
				self.width_btn.set_value(width)
		else:
			self.height_btn.set_value(height)
			self.width_btn.set_value(width)

	def on_release_on_area(self, event, surface, event_x, event_y):
		self.on_motion_on_area(event, surface, event_x, event_y)
		self._directions = ''
		self._ratio_is_inverted = False
		self.build_and_do_op() # technically already done

	############################################################################

	def on_draw_above(self, area, cairo_context):
		if self.apply_to_selection:
			x1 = int(self._x)
			y1 = int(self._y)
		else:
			x1 = 0
			y1 = 0
		x2 = x1 + self._get_width()
		y2 = y1 + self._get_height()
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
			'width': self._get_width(),
			'height': self._get_height()
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

