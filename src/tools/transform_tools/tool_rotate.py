# tool_rotate.py
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

import math
from gi.repository import Gdk
from .abstract_transform_tool import AbstractCanvasTool
from .optionsbar_rotate import OptionsBarRotate

class ToolRotate(AbstractCanvasTool):
	__gtype_name__ = 'ToolRotate'

	def __init__(self, window):
		super().__init__('rotate', _("Rotate"), 'tool-rotate-symbolic', window)
		self.cursor_name = 'pointer'
		self.flip_h = False
		self.flip_v = False
		self.angle_press = 0

		self.add_tool_action_simple('rotate-clockwise', self.on_right_clicked)
		self.add_tool_action_simple('rotate-counter-cw', self.on_left_clicked)
		self.add_tool_action_simple('rotate-flip-h', self.on_horizontal_clicked)
		self.add_tool_action_simple('rotate-flip-v', self.on_vertical_clicked)

	def try_build_pane(self):
		self.pane_id = 'rotate'
		self.window.options_manager.try_add_bottom_pane(self.pane_id, self)

	def build_bottom_pane(self):
		pane = OptionsBarRotate(self)
		self.angle_btn = pane.angle_btn
		self.angle_btn.connect('value-changed', self.on_angle_changed)
		return pane

	def get_options_label(self):
		return _("Rotating options")

	def get_edition_status(self):
		if self.apply_to_selection:
			return _("Rotating the selection")
		else:
			return _("Rotating the canvas")

	def on_tool_selected(self, *args):
		super().on_tool_selected()
		self.flip_h = False
		self.flip_v = False
		self.angle_btn.set_value(0.0)
		self.build_and_do_op() # Show the temp_pixbuf before any event
		if self.apply_to_selection:
			self.cursor_name = 'move'
		else:
			self.cursor_name = 'pointer'
		# the pane is updated by the window according to self.apply_to_selection

	############################################################################

	def on_press_on_area(self, event, surface, event_x, event_y):
		if not self.apply_to_selection:
			if event.button == 1:
				self.on_left_clicked()
			elif event.button == 3:
				self.on_right_clicked()
			return
		center_x, center_y = self.get_selection().get_center_coords()
		delta_x0 = center_x - event_x
		delta_y0 = center_y - event_y
		press_as_degrees = (math.atan2(delta_x0, delta_y0) * 180) / math.pi
		self.angle_press = self.get_angle() - int(press_as_degrees)

	def on_motion_on_area(self, event, surface, event_x, event_y, render=True):
		if not self.apply_to_selection:
			return
		center_x, center_y = self.get_selection().get_center_coords()
		delta_x = center_x - event_x
		delta_y = center_y - event_y
		release_angle = ( math.atan2(delta_x, delta_y) * 180 ) / math.pi
		self.angle_btn.set_value(int(release_angle) + self.angle_press)
		if render:
			operation = self.build_operation()
			self.do_tool_operation(operation)

	def on_release_on_area(self, event, surface, event_x, event_y):
		self.on_motion_on_area(event, surface, event_x, event_y)

	############################################################################

	def get_angle(self):
		return self.angle_btn.get_value_as_int()

	def on_right_clicked(self, *args):
		angle = self.get_normalized_angle()
		self.angle_btn.set_value(angle - 90)

	def on_left_clicked(self, *args):
		angle = self.get_normalized_angle()
		self.angle_btn.set_value(angle + 90)

	def on_vertical_clicked(self, *args):
		self.flip_v = not self.flip_v
		self.build_and_do_op()

	def on_horizontal_clicked(self, *args):
		self.flip_h = not self.flip_h
		self.build_and_do_op()

	def get_normalized_angle(self, *args):
		angle = self.get_angle() % 360
		angle = int(angle/90) * 90
		return angle

	def on_angle_changed(self, *args):
		if self.get_angle() == 360 or self.get_angle() == -360:
			self.angle_btn.set_value(0)
		self.build_and_do_op()

	############################################################################

	def on_draw_above(self, area, cairo_context):
		x1 = 0
		y1 = 0
		x2 = x1 + self.get_image().temp_pixbuf.get_width()
		y2 = y1 + self.get_image().temp_pixbuf.get_height()
		x1, x2, y1, y2 = self.get_image().get_corrected_coords(x1, x2, y1, y2, \
		                                         self.apply_to_selection, False)
		self._draw_temp_pixbuf(cairo_context, x1, y1)

	############################################################################

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'is_selection': self.apply_to_selection,
			'is_preview': True,
			'local_dx': 0,
			'local_dy': 0,
			'angle': self.get_angle(),
			'flip_h': self.flip_h,
			'flip_v': self.flip_v
		}
		return operation

	def do_tool_operation(self, operation):
		self.start_tool_operation(operation)
		angle = operation['angle']
		flip_h = operation['flip_h']
		flip_v = operation['flip_v']
		if operation['is_selection']:
			source_pixbuf = self.get_selection_pixbuf()
		else:
			source_pixbuf = self.get_main_pixbuf()

		if angle < 0:
			angle += 360
		gdk_rotation = int(angle / 90) * 90
		cairo_rotation = angle % 90
		# print('angle:', angle)
		# print('gdk_rotation:', gdk_rotation)
		# print('cairo_rotation:', cairo_rotation)

		# Image rotation, using the method from GdkPixbuf.Pixbuf
		new_pixbuf = source_pixbuf.rotate_simple(gdk_rotation)

		# Image flipping (horizontal or vertical "mirroring")
		if flip_h:
			new_pixbuf = new_pixbuf.flip(True)
		if flip_v:
			new_pixbuf = new_pixbuf.flip(False)

		# Image rotation, using methods from cairo.Context (only if needed)
		if cairo_rotation != 0:
			surface0 = Gdk.cairo_surface_create_from_pixbuf(new_pixbuf, 0, None)
			surface0.set_device_scale(self.scale_factor(), self.scale_factor())
			coefs = self._get_rotation_matrix(cairo_rotation, \
			                        surface0.get_width(), surface0.get_height())
			new_surface = self.get_deformed_surface(surface0, coefs)
			new_pixbuf = Gdk.pixbuf_get_from_surface(new_surface, 0, 0, \
			                  new_surface.get_width(), new_surface.get_height())

		self.get_image().set_temp_pixbuf(new_pixbuf)
		self.common_end_operation(operation)

	def _get_rotation_matrix(self, angle, width, height):
		"""Transform an angle (in degrees) to the xx/yx/xy/yy coefs expected by
		cairo. Due to previously performed modifications to the data, the angle
		will be between 0 (excluded) and 90 (excluded)."""
		rad = math.pi * angle / 180

		xx = math.cos(rad)
		xy = math.sin(rad)
		yx = -1 * math.sin(rad)
		yy = math.cos(rad)

		x0 = max(0, height * yx)
		y0 = max(0, width * xy)

		return [xx, yx, xy, yy, x0, y0]

	############################################################################
################################################################################

