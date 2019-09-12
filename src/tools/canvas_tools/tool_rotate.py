# tool_rotate.py
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

from gi.repository import Gtk, Gdk
import cairo, math

from .abstract_canvas_tool import AbstractCanvasTool
from .bottombar import DrawingAdaptativeBottomBar

class ToolRotate(AbstractCanvasTool):
	__gtype_name__ = 'ToolRotate'

	def __init__(self, window):
		super().__init__('rotate', _("Rotate"), 'tool-rotate-symbolic', window)
		self.cursor_name = 'not-allowed'
		self.apply_to_selection = False
		self.flip_h = False
		self.flip_v = False
		self.angle_press = 0

		self.add_tool_action_simple('rotate-clockwise', self.on_right_clicked)
		self.add_tool_action_simple('rotate-counter-cw', self.on_left_clicked)
		self.add_tool_action_simple('rotate-flip-h', self.on_horizontal_clicked)
		self.add_tool_action_simple('rotate-flip-v', self.on_vertical_clicked)

	def try_build_panel(self):
		self.panel_id = 'rotate'
		self.window.options_manager.try_add_bottom_panel(self.panel_id, self)

	def build_bottom_panel(self):
		panel = RotateToolPanel(self.window, self)
		self.angle_btn = panel.angle_btn
		self.angle_btn.connect('value-changed', self.on_angle_changed)
		return panel

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
		if self.apply_to_selection:
			self.cursor_name = 'move'
		else:
			self.cursor_name = 'not-allowed'
		# the panel is updated by the window according to self.apply_to_selection

	############################################################################

	def on_press_on_area(self, area, event, surface, event_x, event_y):
		if not self.apply_to_selection:
			return
		delta_x0 = self.get_selection().selection_x - event_x
		delta_y0 = self.get_selection().selection_y - event_y
		press_as_degrees = (math.atan2(delta_x0, delta_y0) * 180) / math.pi
		self.angle_press = self.get_angle() + int(press_as_degrees)

	def on_motion_on_area(self, area, event, surface, event_x, event_y):
		if not self.apply_to_selection:
			return
		delta_x = self.get_selection().selection_x - event_x
		delta_y = self.get_selection().selection_y - event_y
		new_angle = ( math.atan2(delta_x, delta_y) * 180 ) / math.pi
		self.angle_btn.set_value(int(new_angle) - self.angle_press)
		operation = self.build_operation()
		self.do_tool_operation(operation)

	def on_release_on_area(self, area, event, surface, event_x, event_y):
		self.on_motion_on_area(area, event, surface, event_x, event_y)

	############################################################################

	def get_angle(self):
		return self.angle_btn.get_value_as_int()

	def on_right_clicked(self, *args):
		angle = self.get_normalized_angle()
		self.angle_btn.set_value(angle + 90)

	def on_left_clicked(self, *args):
		angle = self.get_normalized_angle()
		self.angle_btn.set_value(angle - 90)

	def on_vertical_clicked(self, *args):
		self.flip_v = not self.flip_v
		self.update_temp_pixbuf()

	def on_horizontal_clicked(self, *args):
		self.flip_h = not self.flip_h
		self.update_temp_pixbuf()

	def get_normalized_angle(self, *args):
		angle = self.get_angle() % 360
		angle = int(angle/90) * 90
		print('get_normalized_angle', angle)
		return angle

	def on_angle_changed(self, *args):
		# XXX pré-traitement ici ?
		self.update_temp_pixbuf()

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'is_selection': self.apply_to_selection,
			'is_preview': True,
			'angle': self.get_angle(),
			'flip_h': self.flip_h,
			'flip_v': self.flip_v
		}
		return operation

	def do_tool_operation(self, operation):
		if operation['tool_id'] != self.id:
			return
		self.restore_pixbuf()
		angle = operation['angle']
		flip_h = operation['flip_h']
		flip_v = operation['flip_v']
		if operation['is_selection']:
			source_pixbuf = self.get_selection_pixbuf()
		else:
			source_pixbuf = self.get_main_pixbuf()

		# print('angle0:', angle)
		if angle % 90 == 0:
			if angle < 0:
				angle += 360
			if angle == 360:
				angle = 0
			new_pixbuf = source_pixbuf.rotate_simple(angle)
		else:
			if angle < 180:
				angle += 360
			if angle > 180:
				angle -= 360
			# print('angle2:', angle)
			source_surface = Gdk.cairo_surface_create_from_pixbuf(source_pixbuf, 0, None)
			p_xx, p_yx, p_xy, p_yy, p_x0, p_y0 = self.get_rotation_matrix( \
			     angle, source_surface.get_width(), source_surface.get_height())
			new_surface = self.get_deformed_surface(source_surface, \
			                                 p_xx, p_yx, p_xy, p_yy, p_x0, p_y0)
			new_pixbuf = Gdk.pixbuf_get_from_surface(new_surface, 0, 0, \
			                  new_surface.get_width(), new_surface.get_height())

		if flip_h:
			new_pixbuf = new_pixbuf.flip(True)
		if flip_v:
			new_pixbuf = new_pixbuf.flip(False)
		self.get_image().set_temp_pixbuf(new_pixbuf)
		self.common_end_operation(operation['is_preview'], operation['is_selection'])

	def get_rotation_matrix(self, angle, width, height):
		rad = math.pi * angle / 180
		print('rad', rad)
		xx = math.cos(rad)
		xy = math.sin(rad)
		yx = -1 * math.sin(rad)
		yy = math.cos(rad)

		if rad % (2 * math.pi) == 0:
			x0 = 0
			y0 = 0
		elif rad > math.pi/-2 and rad < math.pi/2:
			x0 = height * yx
			y0 = width * xy
		# elif rad > math.pi/2 and rad < math.pi:
		# 	x0 = height * yx
		# 	y0 = width * xy
		else:
			self.window.prompt_message(True, 'bruh moment: angle bad')
			x0 = height * yx # XXX
			y0 = width * xy # XXX

		x0 = max(0, x0)
		y0 = max(0, y0)

		return xx, yx, xy, yy, x0, y0

	############################################################################
################################################################################

class RotateToolPanel(DrawingAdaptativeBottomBar):
	__gtype_name__ = 'RotateToolPanel'

	def __init__(self, window, rotate_tool):
		super().__init__()
		self.window = window
		# knowing the tool is needed because the panel doesn't compact the same
		# way if it's applied to the selection
		self.rotate_tool = rotate_tool
		builder = self.build_ui('tools/ui/tool_rotate.ui')
		self.angle_btn = builder.get_object('angle_btn')
		self.more_btn = builder.get_object('more_btn')
		self.angle_box = builder.get_object('angle_box')
		self.rotate_box = builder.get_object('rotate_box')
		self.flip_box = builder.get_object('flip_box')

	def init_adaptability(self):
		super().init_adaptability()
		temp_limit_size = self.centered_box.get_preferred_width()[0] + \
		                    self.cancel_btn.get_preferred_width()[0] + \
		                     self.apply_btn.get_preferred_width()[0]
		self.set_limit_size(temp_limit_size)

	def update_for_new_tool(self, tool):
		self.set_compact(self.is_narrow)

	def toggle_options_menu(self):
		if self.more_btn.get_visible():
			self.more_btn.set_active(not self.more_btn.get_active())

	def set_compact(self, state):
		super().set_compact(state)
		if self.rotate_tool.apply_to_selection:
			self.more_btn.set_visible(state)
			self.angle_box.set_visible(True)
			self.rotate_box.set_visible(not state)
			self.flip_box.set_visible(not state)
		else:
			self.more_btn.set_visible(False)
			self.angle_box.set_visible(False)
			self.rotate_box.set_visible(True)
			self.flip_box.set_visible(True)

	############################################################################
################################################################################

