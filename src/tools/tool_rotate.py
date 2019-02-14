# tool_rotate.py # XXX
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

from gi.repository import Gtk, Gdk, Gio, GLib

from .tools import ToolTemplate

class ToolRotate(ToolTemplate):
	__gtype_name__ = 'ToolRotate'

	implements_panel = True

	def __init__(self, window):
		super().__init__('rotate', _("Rotate"), 'view-refresh-symbolic', window)
		self.need_temp_pixbuf = True

		self.add_tool_action_simple('rotate_apply', self.on_apply)

		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/Drawing/tools/ui/tool_rotate.ui')
		self.bottom_panel = builder.get_object('bottom-panel')
		self.angle_btn = builder.get_object('angle_btn')
		self.angle_label = builder.get_object('angle_label')
		self.right_btn = builder.get_object('right_btn')
		self.left_btn = builder.get_object('left_btn')

		self.angle_btn.connect('value-changed', self.on_angle_changed)
		self.right_btn.connect('clicked', self.on_right_clicked)
		self.left_btn.connect('clicked', self.on_left_clicked)

		self.window.bottom_panel_box.add(self.bottom_panel)

	def get_panel(self):
		return self.bottom_panel

	def get_edition_status(self):
		if self.rotate_selection:
			return _("Rotating the selection")
		else:
			return _("Rotating the canvas")

	def on_tool_selected(self, *args):
		self.rotate_selection = (self.window.hijacker_id is not None)
		self.angle_btn.set_value(0.0)
		if False:
		# if self.rotate_selection:
			self.angle_btn.set_visible(True)
			self.angle_label.set_visible(True)
			self.right_btn.set_visible(False)
			self.left_btn.set_visible(False)
		else:
			self.angle_btn.set_visible(False)
			self.angle_label.set_visible(False)
			self.right_btn.set_visible(True)
			self.left_btn.set_visible(True)
		self.update_temp_pixbuf()

	def on_apply(self, *args):
		self.restore_pixbuf()
		if self.rotate_selection:
			self.get_image().selection_pixbuf = self.get_selection_pixbuf().rotate_simple(self.get_angle())
			self.window.former_tool().on_confirm_hijacked_modif()
		else:
			self.get_image().set_main_pixbuf(self.get_main_pixbuf().rotate_simple(self.get_angle()))
			#self.apply_to_pixbuf()
			self.restore_pixbuf()
			self.window.back_to_former_tool()

	def get_angle(self):
		return self.angle_btn.get_value_as_int()

	def update_temp_pixbuf(self):
		angle = self.get_angle()
		if self.rotate_selection:
			self.get_image().set_temp_pixbuf(self.get_selection_pixbuf().rotate_simple(angle))
		else:
			self.get_image().set_temp_pixbuf(self.get_main_pixbuf().rotate_simple(angle))

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
		# if not self.rotate_selection:
			angle = int(angle/90) * 90
		if angle != self.get_angle():
			self.angle_btn.set_value(angle)
		self.update_temp_pixbuf()
		self.update_area()

	def update_area(self):
		self.update_temp_pixbuf()
		# if self.rotate_selection:
		# 	self.set_edition_state('temp-as-selection')
		# else:
		# 	self.set_edition_state('temp-as-main')
		self.non_destructive_show_modif()

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'is_selection': self.rotate_selection,
			'pixbuf': None,
			'angle': self.get_angle()
		}
		return operation

	def do_tool_operation(self, operation):
		if operation['tool_id'] != self.id:
			return
		self.restore_pixbuf()
		cairo_context = cairo.Context(self.get_surface())
		# TODO 
