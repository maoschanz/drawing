# abstract_canvas_tool.py
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

from gi.repository import Gtk, Gdk, GdkPixbuf
import cairo

from .abstract_tool import ToolTemplate

class AbstractCanvasTool(ToolTemplate):
	__gtype_name__ = 'AbstractCanvasTool'

	def __init__(self, tool_id, label, icon_name, window, **kwargs):
		super().__init__(tool_id, label, icon_name, window)
		self.implements_panel = True
		self.menu_id = 1
		self.centered_box = None
		self.needed_width_for_long = 0
		self.accept_selection = True

	def adapt_to_window_size(self, available_width):
		if self.centered_box is None:
			return
		if self.centered_box.get_orientation() == Gtk.Orientation.HORIZONTAL:
			self.needed_width_for_long = self.centered_box.get_preferred_width()[0] + \
				self.cancel_btn.get_allocated_width() + \
				self.apply_btn.get_allocated_width()
		if self.needed_width_for_long > 0.8 * available_width:
			self.centered_box.set_orientation(Gtk.Orientation.VERTICAL)
		else:
			self.centered_box.set_orientation(Gtk.Orientation.HORIZONTAL)

	def update_temp_pixbuf(self):
		operation = self.build_operation()
		self.do_tool_operation(operation)

	def on_apply_temp_pixbuf_tool_operation(self, *args):
		self.restore_pixbuf()
		operation = self.build_operation()
		self.apply_operation(operation)
		self.window.force_selection()

	def apply_operation(self, operation):
		operation['is_preview'] = False
		super().apply_operation(operation)


