# tool_crop.py
#
# Copyright 2018-2022 Romain F. T.
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

from gi.repository import Gdk, GdkPixbuf
from .abstract_transform_tool import AbstractCanvasTool
from .optionsbar_crop import OptionsBarCrop
from .utilities_overlay import utilities_show_handles_on_context
from .utilities_colors import utilities_rgba_to_hexadecimal, \
                              utilities_gdk_rgba_to_color_array

class ToolCrop(AbstractCanvasTool):
	__gtype_name__ = 'ToolCrop'

	def __init__(self, window):
		super().__init__('crop', _("Crop"), 'tool-crop-symbolic', window)
		self.cursor_name = 'not-allowed'
		self._x = self.x_press = self.x_motion = 0
		self._y = self.y_press = self.y_motion = 0
		self._unclicked = True # the lock will prevent operations coming from
		# the 'value-changed' signals, to avoid infinite loops
		self.add_tool_action_enum('crop-expand', 'initial')

	def try_build_pane(self):
		self.pane_id = 'crop'
		self.window.options_manager.try_add_bottom_pane(self.pane_id, self)

	def build_bottom_pane(self):
		bar = OptionsBarCrop()
		self.height_btn = bar.height_btn
		self.width_btn = bar.width_btn
		self.width_btn.connect('value-changed', self.on_width_changed)
		self.height_btn.connect('value-changed', self.on_height_changed)
		return bar

	def get_options_label(self):
		# The options of the "crop" tool are all about how to expand the canvas,
		# hence this label.
		return _("Expanding options")

	def get_editing_tips(self):
		label_direction = _("The sides you'll crop are hinted by the mouse pointer")

		label_modifiers = None
		if self.apply_to_selection:
			label_action = _("Cropping the selection")
			label_confirm = None
		else:
			label_action = _("Cropping or expanding the canvas")
			label_confirm = self.label + " - " + \
			                         _("Don't forget to confirm the operation!")
			if not self.get_image().get_mouse_is_pressed():
				label_modifiers = _("Press <Alt>, <Shift>, or both, to " + \
				                      "quickly change the 'expand with' option")

		full_list = [label_action, label_direction, label_confirm, label_modifiers]
		return list(filter(None, full_list))

	############################################################################

	def on_tool_selected(self, *args):
		super().on_tool_selected()
		self._x = 0
		self._y = 0
		if self.apply_to_selection:
			self._init_if_selection()
		else:
			self._init_if_main()
		self._update_expansion_rgba()
		self.width_btn.set_value(self._original_width)
		self.height_btn.set_value(self._original_height)
		self.set_action_sensitivity('crop-expand', not self.apply_to_selection)
		self.build_and_do_op()

	def _init_if_selection(self):
		self._original_width = self.get_selection_pixbuf().get_width()
		self._original_height = self.get_selection_pixbuf().get_height()
		self.width_btn.set_range(1, self._original_width)
		self.height_btn.set_range(1, self._original_height)

	def _init_if_main(self):
		self._original_width = self.get_image().get_pixbuf_width()
		self._original_height = self.get_image().get_pixbuf_height()
		self.width_btn.set_range(1, 10 * self._original_width)
		self.height_btn.set_range(1, 10 * self._original_height)

	############################################################################

	def _get_width(self):
		return self.width_btn.get_value_as_int()

	def _get_height(self):
		return self.height_btn.get_value_as_int()

	def on_width_changed(self, *args):
		if self._unclicked:
			self.build_and_do_op()

	def on_height_changed(self, *args):
		if self._unclicked:
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
		self.set_directional_cursor(event.x, event.y, True)

	def on_press_on_area(self, event, surface, event_x, event_y):
		self.x_press = self.x_motion = event_x
		self.y_press = self.y_motion = event_y
		self._unclicked = False
		self._update_expansion_rgba(event.button)

		self.update_modifier_state(event.state)
		if 'SHIFT' in self._modifier_keys and 'ALT' in self._modifier_keys:
			self._force_expansion_rgba('secondary', event.button)
		elif 'SHIFT' in self._modifier_keys:
			self._force_expansion_rgba('alpha')
		elif 'ALT' in self._modifier_keys:
			self._force_expansion_rgba('initial')

		if event.button == 3:
			self._directions = ''
			self.cursor_name = 'move'
			self.window.set_cursor(True)
			# interacting with the right click will move instead of cropping

	def on_motion_on_area(self, event, surface, event_x, event_y, render=True):
		delta_x = event_x - self.x_motion
		delta_y = event_y - self.y_motion

		render = render or (event_x % 4 == 0) # artificially less restrictive

		if self._directions == '':
			# the user interacts with the central part of the image, or uses the
			# right-click, to adjust the canvas position.
			self._x -= delta_x
			self._y -= delta_y
			self.x_motion = event_x
			self.y_motion = event_y

			if self.apply_to_selection:
				self._x = max(0, self._x)
				self._y = max(0, self._y)
				self._x = min(self._x, self._original_width - self._get_width())
				self._y = min(self._y, self._original_height - self._get_height())
			else:
				self._x = max(self._get_width() * -1, self._x)
				self._y = max(self._get_height() * -1, self._y)
				self._x = min(self._get_width() * 2, self._x)
				self._y = min(self._get_height() * 2, self._y)

			if render and not self.apply_to_selection:
				self.build_and_do_op()
			return

		if 'n' in self._directions:
			self.move_north(delta_y)
		if 's' in self._directions:
			self.move_south(delta_y)
		if 'w' in self._directions:
			self.move_west(delta_x)
		if 'e' in self._directions:
			self.move_east(delta_x)

		if self.apply_to_selection:
			self._x = max(0, self._x)
			self._y = max(0, self._y)
			width = min(self._original_width - self._x, self._get_width())
			height = min(self._original_height - self._y, self._get_height())
			self.width_btn.set_value(width)
			self.height_btn.set_value(height)

		self.x_motion = event_x
		self.y_motion = event_y
		# not adding the condition would be a better UX but slower to compute
		if render and not self.apply_to_selection:
			self.build_and_do_op()

	def on_release_on_area(self, event, surface, event_x, event_y):
		self._unclicked = True
		self.build_and_do_op()
		self._scroll_to_end(event_x - self.x_press, event_y - self.y_press)
		self.window.set_cursor(False)

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
		if not self.apply_to_selection:
			self._draw_temp_pixbuf(cairo_context, x1, y1)
		thickness = self.get_overlay_thickness()
		utilities_show_handles_on_context(cairo_context, x1, x2, y1, y2, thickness)

	############################################################################

	def build_selection_fit_operation(self):
		"""Special way to build an operation, not from the present crop tool,
		but from the selection menu. The parameters are determined automatically
		from the state of the selection manager."""
		self._update_expansion_rgba()
		s = self.get_selection()
		new_x = min(0, s.selection_x)
		new_y = min(0, s.selection_y)

		s_width = max(0, s.selection_x) + s.selection_pixbuf.get_width()
		new_width = max(-1 * new_x + self.get_main_pixbuf().get_width(), s_width)

		s_height = max(0, s.selection_y) + s.selection_pixbuf.get_height()
		new_height = max(-1 * new_y + self.get_main_pixbuf().get_height(), s_height)

		operation = {
			'tool_id': self.id,
			'is_selection': False,
			'is_preview': False,
			'is_etf': True,
			'local_dx': int(new_x),
			'local_dy': int(new_y),
			'width': new_width,
			'height': new_height,
			'rgba': self._expansion_rgba
		}
		return operation

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'is_selection': self.apply_to_selection,
			'is_preview': True,
			'is_etf': False,
			'local_dx': int(self._x),
			'local_dy': int(self._y),
			'width': self._get_width(),
			'height': self._get_height(),
			'rgba': self._expansion_rgba
		}
		return operation

	def do_tool_operation(self, operation):
		self.start_tool_operation(operation)
		x = operation['local_dx']
		y = operation['local_dy']
		width = operation['width']
		height = operation['height']

		rgba_array = utilities_gdk_rgba_to_color_array(operation['rgba'])
		rgba_array[3] *= 255
		hexa_rgba = utilities_rgba_to_hexadecimal(*rgba_array)

		is_selection = operation['is_selection']
		if is_selection:
			source_pixbuf = self.get_selection_pixbuf()
		else:
			source_pixbuf = self.get_main_pixbuf()
		self.get_image().set_temp_pixbuf(source_pixbuf.copy())
		self._crop_temp_pixbuf(x, y, width, height, is_selection, hexa_rgba)
		if operation['is_etf']:
			# Case of an "expand to fit" action
			s_pixbuf = self.get_selection_pixbuf()
			self.get_selection().update_from_transform_tool(s_pixbuf, -1 * x, -1 * y)
		self.common_end_operation(operation)

	def _crop_temp_pixbuf(self, x, y, width, height, is_selection, hexa_rgba):
		"""Crop and/or expand the temp pixbuf according to given parameters."""

		# Coordinates of the origin of the source pixbuf (temp_p)
		src_x = max(x, 0)
		src_y = max(y, 0)

		# Coordinates of the origin of the destination pixbuf (new_pixbuf)
		if is_selection:
			dest_x = 0
			dest_y = 0
		else:
			dest_x = max(-1 * x, 0)
			dest_y = max(-1 * y, 0)

		# Dotted lines == new sizes; plain lines == old sizes.
		#
		# If the origin has been cropped, `src` == the new coordinates, and
		# `dest` == 0 (in the considered direction x or y):
		#
		# dest____________________
		# |                       |
		# |  src------------------|
		# |   ⁝                   |
		# |___⁝___________________|
		#
		# With the selection, it's not possible to expand, so we're always in
		# this first case, with `dest` == 0.
		# Else (if it hasn't moved, or if it has been expanded) `src` has to be
		# 0 (because the coordinates GdkPixbuf will use can't be negative), and
		# `dest` is (-1 * the new coordinates):
		#
		# dest---------------------
		# ⁝                       ⁝
		# ⁝  src__________________⁝
		# ⁝   |                   |
		# ⁝___|___________________|
		#
		# The sign inversion is completely artificial (again: it's because the
		# coordinates GdkPixbuf will use can't be negative).

		# Initialisation of an EMPTY pixbuf with the wanted size and color
		new_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, \
		                                                          width, height)
		new_pixbuf.fill(hexa_rgba)

		temp_p = self.get_image().temp_pixbuf
		# The width/height we want (measured from the respective origins of the
		# `src` and the `dest` rectangles)
		min_w = min(width - dest_x, temp_p.get_width() - src_x)
		min_h = min(height - dest_y, temp_p.get_height() - src_y)

		# Copy an area of the source pixbuf `temp_p`; the area starts at `src_*`
		# and has the dimensions `min_*`. It's painted on the destination pixbuf
		# (`new_pixbuf`) starting at the coordinates `dest_*`.
		temp_p.copy_area(src_x, src_y, min_w, min_h, new_pixbuf, dest_x, dest_y)
		self.get_image().set_temp_pixbuf(new_pixbuf)

	############################################################################
################################################################################

