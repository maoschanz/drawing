# tool_crop.py
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

from gi.repository import Gdk, GdkPixbuf
from .abstract_transform_tool import AbstractCanvasTool
from .optionsbar_crop import OptionsBarCrop
from .utilities_overlay import utilities_show_handles_on_context

class ToolCrop(AbstractCanvasTool):
	__gtype_name__ = 'ToolCrop'

	def __init__(self, window):
		super().__init__('crop', _("Crop"), 'tool-crop-symbolic', window)
		self.cursor_name = 'not-allowed'
		self.x_press = 0
		self.y_press = 0
		self.unclicked = True
		self.add_tool_action_enum('crop-expand', 'initial')
		self._expansion_color = 0 # transparent black, will be updated later

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
		return _("Cropping options")

	def get_edition_status(self):
		if self.apply_to_selection:
			return _("Cropping the selection")
		else:
			return _("Cropping the canvas")

	############################################################################

	def on_tool_selected(self, *args):
		super().on_tool_selected()
		self._x = 0
		self._y = 0
		if self.apply_to_selection:
			self._init_if_selection()
		else:
			self._init_if_main()
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

	def _update_expansion_color(self, event_btn=1):
		"""When the canvas grows, the color of the new pixels is parametrable"""
		color_type = self.get_option_value('crop-expand')
		if color_type == 'initial':
			exp_rgba = self.get_image().get_initial_rgba()
		elif color_type == 'secondary' and event_btn == 1:
			exp_rgba = self.window.options_manager.get_right_color()
		elif color_type == 'secondary' and event_btn == 3:
			exp_rgba = self.window.options_manager.get_left_color()
		else: # color_type == 'alpha':
			exp_rgba = Gdk.RGBA(red=1.0, green=1.0, blue=1.0, alpha=0.0)
		self._expansion_color = self._rgba_as_hexa_int(exp_rgba)

	def _rgba_as_hexa_int(self, gdk_rgba):
		"""The method GdkPixbuf.Pixbuf.fill wants an hexadecimal integer whose
		format is 0xrrggbbaa so here are ugly binary operators."""
		r = int(255 * gdk_rgba.red)
		g = int(255 * gdk_rgba.green)
		b = int(255 * gdk_rgba.blue)
		a = int(255 * gdk_rgba.alpha)
		return (((((r << 8) + g) << 8) + b) << 8) + a

	############################################################################

	def _get_width(self):
		return self.width_btn.get_value_as_int()

	def _get_height(self):
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
		self.x_press = event_x
		self.y_press = event_y
		self.unclicked = False
		self._update_expansion_color(event.button)

	def on_motion_on_area(self, event, surface, event_x, event_y, render=True):
		delta_x = int(event_x - self.x_press)
		delta_y = int(event_y - self.y_press)

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
			width = min(self._original_width - self._x, self._get_width())
			height = min(self._original_height - self._y, self._get_height())
			self.width_btn.set_value(width)
			self.height_btn.set_value(height)

		self.x_press = event_x
		self.y_press = event_y
		# not adding the condition would be a better UX but slower to compute
		if render and not self.apply_to_selection:
			self.build_and_do_op()

	def on_release_on_area(self, event, surface, event_x, event_y):
		self.unclicked = True
		self.build_and_do_op()
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
		self._update_expansion_color()
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
			'rgba': self._expansion_color
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
			'rgba': self._expansion_color
		}
		return operation

	def do_tool_operation(self, operation):
		self.start_tool_operation(operation)
		x = operation['local_dx']
		y = operation['local_dy']
		width = operation['width']
		height = operation['height']
		rgba = operation['rgba']
		is_selection = operation['is_selection']
		if is_selection:
			source_pixbuf = self.get_selection_pixbuf()
		else:
			source_pixbuf = self.get_main_pixbuf()
		self.get_image().set_temp_pixbuf(source_pixbuf.copy())
		self._crop_temp_pixbuf(x, y, width, height, is_selection, rgba)
		if operation['is_etf']:
			s_pixbuf = self.get_selection_pixbuf()
			self.get_selection().update_from_transform_tool(s_pixbuf, -1 * x, -1 * y)
		self.common_end_operation(operation)

	def _crop_temp_pixbuf(self, x, y, width, height, is_selection, rgba):
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

		# Dotted lines == new sizes; plain line == old sizes.
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
		new_pixbuf.fill(rgba)

		temp_p = self.get_image().temp_pixbuf
		# The width/height we want (mesured from the respective origins of the
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

