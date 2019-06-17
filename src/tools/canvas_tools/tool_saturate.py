# tool_saturate.py
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

from .abstract_canvas_tool import AbstractCanvasTool

class ToolSaturate(AbstractCanvasTool):
	__gtype_name__ = 'ToolSaturate'

	def __init__(self, window):
		super().__init__('saturate', _("Saturate"), 'tool-saturate-symbolic', window)
		self.cursor_name = 'not-allowed'
		self.apply_to_selection = False

		builder = Gtk.Builder.new_from_resource( \
		              '/com/github/maoschanz/drawing/tools/ui/tool_saturate.ui')
		self.bottom_panel = builder.get_object('bottom-panel')

		self.saturation_btn = builder.get_object('sat_btn')
		self.saturation_btn.connect('value-changed', self.on_sat_changed)

		self.window.bottom_panel_box.add(self.bottom_panel)

	def on_tool_selected(self, *args):
		self.apply_to_selection = self.selection_is_active()
		self.saturation_btn.set_value(100.0)
		self.on_sat_changed()

	def get_saturation(self):
		return self.saturation_btn.get_value()/100

	def on_sat_changed(self, *args):
		self.update_temp_pixbuf()

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'is_selection': self.apply_to_selection,
			'is_preview': True,
			'saturation': self.get_saturation()
		}
		return operation

	def do_tool_operation(self, operation):
		if operation['tool_id'] != self.id:
			return
		self.restore_pixbuf()
		saturation = operation['saturation']
		if operation['is_selection']:
			source_pixbuf = self.get_selection_pixbuf()
		else:
			source_pixbuf = self.get_main_pixbuf()
		self.get_image().set_temp_pixbuf(source_pixbuf.copy())
		temp = self.get_image().get_temp_pixbuf()
		source_pixbuf.saturate_and_pixelate(temp, saturation, False)
		self.common_end_operation(operation['is_preview'], operation['is_selection'])
