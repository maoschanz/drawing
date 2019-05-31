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
import cairo

from .abstract_canvas_tool import AbstractCanvasTool

class ToolRotate(AbstractCanvasTool):
	__gtype_name__ = 'ToolRotate'

	def __init__(self, window):
		super().__init__('rotate', _("Rotate"), 'tool-rotate-symbolic', window)
		self.cursor_name = 'not-allowed'
		self.apply_to_selection = False

		builder = Gtk.Builder.new_from_resource( \
		                '/com/github/maoschanz/drawing/tools/ui/tool_rotate.ui')
		self.bottom_panel = builder.get_object('bottom-panel')
		self.angle_btn = builder.get_object('angle_btn')
		self.angle_label = builder.get_object('angle_label')
		self.right_btn = builder.get_object('right_btn')
		self.left_btn = builder.get_object('left_btn')

		self.angle_btn.connect('value-changed', self.on_angle_changed)
		self.right_btn.connect('clicked', self.on_right_clicked)
		self.left_btn.connect('clicked', self.on_left_clicked)

		self.window.bottom_panel_box.add(self.bottom_panel)

	def get_edition_status(self):
		if self.apply_to_selection:
			return _("Rotating the selection")
		else:
			return _("Rotating the canvas")

	def on_tool_selected(self, *args):
		self.apply_to_selection = self.selection_is_active()
		self.angle_btn.set_value(0.0)
		if False:
		# if self.apply_to_selection:
			self.angle_btn.set_visible(True)
			self.angle_label.set_visible(True)
			self.right_btn.set_visible(False)
			self.left_btn.set_visible(False)
		else:
			self.angle_btn.set_visible(False)
			self.angle_label.set_visible(False)
			self.right_btn.set_visible(True)
			self.left_btn.set_visible(True)
		self.on_angle_changed()

	def get_angle(self):
		return self.angle_btn.get_value_as_int()

	def on_right_clicked(self, *args):
		self.angle_btn.set_value(self.get_angle() + 90)

	def on_left_clicked(self, *args):
		self.angle_btn.set_value(self.get_angle() - 90)

	def on_angle_changed(self, *args):
		angle = self.get_angle()
		angle = angle % 360
		if angle < 0:
			angle += 180
		if True:
		# if not self.apply_to_selection:
			angle = int(angle/90) * 90
		if angle != self.get_angle():
			self.angle_btn.set_value(angle)
		self.update_temp_pixbuf()

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'is_selection': self.apply_to_selection,
			'is_preview': True,
			'angle': self.get_angle()
		}
		return operation

	def do_tool_operation(self, operation):
		if operation['tool_id'] != self.id:
			return
		self.restore_pixbuf()
		angle = operation['angle']
		if operation['is_selection']:
			source_pixbuf = self.get_selection_pixbuf()
		else:
			source_pixbuf = self.get_main_pixbuf()
		self.get_image().set_temp_pixbuf(source_pixbuf.rotate_simple(angle))

		if operation['is_preview']:
			self.finish_pixbuf_tool_operation_preview(operation['is_selection'])

