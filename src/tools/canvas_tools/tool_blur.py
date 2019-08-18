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

from .utilities import utilities_fast_blur

from .abstract_canvas_tool import AbstractCanvasTool
from .bottombar import DrawingAdaptativeBottomBar

class ToolBlur(AbstractCanvasTool):
	__gtype_name__ = 'ToolBlur'

	def __init__(self, window):
		super().__init__('blur', _("Blur"), 'tool-blur-symbolic', window)
		self.cursor_name = 'not-allowed'
		self.apply_to_selection = False

	def try_build_panel(self):
		self.panel_id = 'blur'
		self.window.options_manager.try_add_bottom_panel(self.panel_id, self)

	def build_bottom_panel(self):
		bar = DrawingAdaptativeBottomBar()
		builder = bar.build_ui('tools/ui/tool_blur.ui')
		# ... TODO
		#
		# bar.widgets_narrow = []
		# bar.widgets_wide = []
		#
		#

		self.blur_btn = builder.get_object('blur_btn')
		self.blur_btn.connect('activate', self.on_blur_changed)
		# self.blur_btn.connect('value-changed', self.on_blur_changed)

		return bar

	def on_tool_selected(self, *args):
		super().on_tool_selected()
		self.on_blur_changed()

	def get_blur_radius(self):
		return int( self.blur_btn.get_value() )

	def on_blur_changed(self, *args):
		self.update_temp_pixbuf()

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'is_selection': self.apply_to_selection,
			'is_preview': True,
			'radius': self.get_blur_radius()
		}
		return operation

	def do_tool_operation(self, operation):
		if operation['tool_id'] != self.id:
			return
		self.restore_pixbuf()
		blur_radius = operation['radius']
		if operation['is_selection']:
			source_pixbuf = self.get_selection_pixbuf()
		else:
			source_pixbuf = self.get_main_pixbuf()
		surface = Gdk.cairo_surface_create_from_pixbuf(source_pixbuf, 0, None)
		blurred_surface = utilities_fast_blur(surface, blur_radius, 1)
		blurred_pixbuf = Gdk.pixbuf_get_from_surface(blurred_surface, 0, 0, \
		              blurred_surface.get_width(), blurred_surface.get_height())
		self.get_image().set_temp_pixbuf(blurred_pixbuf)
		self.common_end_operation(operation['is_preview'], operation['is_selection'])


