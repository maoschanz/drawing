# tool_flip.py
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

from .tools import ToolTemplate

class ToolFlip(ToolTemplate):
	__gtype_name__ = 'ToolFlip'

	implements_panel = True

	def __init__(self, window):
		super().__init__('flip', _("Flip"), 'tool-flip-symbolic', window, True)
		self.cursor_name = 'not-allowed'
		self.apply_to_selection = False
		self.flip_h = False
		self.flip_v = False

		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/drawing/tools/ui/tool_flip.ui')
		self.bottom_panel = builder.get_object('bottom-panel')

		self.horizontal_btn = builder.get_object('horizontal_btn')
		self.vertical_btn = builder.get_object('vertical_btn')
		self.horizontal_btn.connect('clicked', self.on_horizontal_clicked)
		self.vertical_btn.connect('clicked', self.on_vertical_clicked)

		self.window.bottom_panel_box.add(self.bottom_panel)

	def on_vertical_clicked(self, *args):
		self.flip_v = not self.flip_v
		self.update_temp_pixbuf()

	def on_horizontal_clicked(self, *args):
		self.flip_h = not self.flip_h
		self.update_temp_pixbuf()

	def on_tool_selected(self, *args):
		self.apply_to_selection = (self.window.hijacker_id is not None)
		self.flip_h = False
		self.flip_v = False
		self.update_temp_pixbuf()

	def update_temp_pixbuf(self):
		operation = self.build_operation()
		self.do_tool_operation(operation)

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'is_selection': self.apply_to_selection,
			'flip_h': self.flip_h,
			'flip_v': self.flip_v
		}
		return operation

	def do_tool_operation(self, operation):
		if operation['tool_id'] != self.id:
			return
		self.restore_pixbuf()
		flip_h = operation['flip_h']
		flip_v = operation['flip_v']
		if operation['is_selection']:
			source_pixbuf = self.get_selection_pixbuf()
		else:
			source_pixbuf = self.get_main_pixbuf()
		self.get_image().set_temp_pixbuf(source_pixbuf.copy())
		preview = self.get_image().get_temp_pixbuf()
		if flip_h and flip_v:
			preview = preview.flip(True)
			preview = preview.flip(False)
			self.get_image().set_temp_pixbuf(preview)
		elif flip_h:
			self.get_image().set_temp_pixbuf(preview.flip(True))
		elif flip_v:
			self.get_image().set_temp_pixbuf(preview.flip(False))
		self.finish_temp_pixbuf_tool_operation(operation['is_selection'])

