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
from .bottombar import DrawingAdaptativeBottomBar

class ToolSaturate(AbstractCanvasTool):
	__gtype_name__ = 'ToolSaturate'

	def __init__(self, window):
		super().__init__('saturate', _("Saturate"), 'tool-saturate-symbolic', window)
		self.cursor_name = 'not-allowed'
		self.apply_to_selection = False

	def try_build_panel(self):
		self.panel_id = 'saturate'
		self.window.options_manager.try_add_bottom_panel(self.panel_id, self)

	def build_bottom_panel(self):
		bar = DrawingAdaptativeBottomBar()
		builder = bar.build_ui('tools/ui/tool_saturate.ui')
		# ... TODO
		#
		# bar.widgets_narrow = []
		# bar.widgets_wide = []
		#
		self.saturation_btn = builder.get_object('sat_btn')
		self.saturation_btn.connect('value-changed', self.on_sat_changed)
		#
		#
		return bar

	def on_tool_selected(self, *args):
		super().on_tool_selected()
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
