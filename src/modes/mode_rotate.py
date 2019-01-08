# crop.py
#
# Copyright 2018 Romain F. T.
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

from .modes import ModeTemplate

class ModeRotate(ModeTemplate):
	__gtype_name__ = 'ModeRotate'

	def __init__(self, window):
		super().__init__(window)

		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/Drawing/modes/ui/mode_rotate.ui')
		self.bottom_panel = builder.get_object('bottom-panel')
		self.angle_btn = builder.get_object('angle_btn')
		self.angle_btn.connect('value-changed', self.on_angle_changed)

	def get_panel(self):
		return self.bottom_panel

	def get_edition_status(self):
		if self.rotate_selection:
			return _("Rotating the selection")
		else:
			return _("Rotating the canvas")

	def on_mode_selected(self, *args):
		self.rotate_selection = args[0]
		self.set_action_sensitivity('active_tool', False)

	def on_apply_mode(self):
		if self.rotate_selection:
			self.window.active_tool().rotate_pixbuf(self.get_angle())
		else:
			self.window.rotate_pixbuf(self.get_angle())

	def get_angle(self):
		return self.angle_btn.get_value_as_int()

	def on_draw(self, area, cairo_context, main_x, main_y):
		angle = self.get_angle()
		if self.rotate_selection:
			self.window.temporary_pixbuf = self.window.active_tool().selection_pixbuf.rotate_simple(angle)
			self.window.active_tool().delete_temp()
			selection_x = self.window.active_tool().selection_x
			selection_y = self.window.active_tool().selection_y
			self.window.show_pixbuf_content_at(self.window.temporary_pixbuf, selection_x, selection_y)
			super().on_draw(area, cairo_context, main_x, main_y)
		else:
			self.window.temporary_pixbuf = self.window.main_pixbuf.rotate_simple(angle)
			Gdk.cairo_set_source_pixbuf(cairo_context, self.window.temporary_pixbuf, 0, 0) # XXX c'est là pour le zoom non ? en négatif
			cairo_context.paint()

	def on_angle_changed(self, *args):
		if self.get_angle() % 90 != 0:
			self.angle_btn.set_value(int(self.get_angle() / 90) * 90)
		if self.rotate_selection:
			self.window.use_stable_pixbuf()
		self.non_destructive_show_modif()
