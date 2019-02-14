# tool_flip.py # XXX
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

from gi.repository import Gtk, Gdk, Gio, GLib, GdkPixbuf

from .tools import ToolTemplate

class ToolFlip(ToolTemplate):
	__gtype_name__ = 'ToolFlip'

	implements_panel = True

	def __init__(self, window):
		super().__init__('flip', _("Flip"), 'object-flip-horizontal-symbolic', window, True)
		self.need_temp_pixbuf = True

		self.add_tool_action_simple('flip_apply', self.on_apply)

		self.flip_selection = False
		self.flip_h = False
		self.flip_v = False

		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/Drawing/tools/ui/tool_flip.ui')
		self.bottom_panel = builder.get_object('bottom-panel')

		self.horizontal_btn = builder.get_object('horizontal_btn')
		self.vertical_btn = builder.get_object('vertical_btn')
		self.horizontal_btn.connect('clicked', self.on_horizontal_clicked)
		self.vertical_btn.connect('clicked', self.on_vertical_clicked)

		self.window.bottom_panel_box.add(self.bottom_panel)

	def get_panel(self): # FIXME utile ??
		return self.bottom_panel

	def on_vertical_clicked(self, *args):
		self.flip_v = not self.flip_v
		self.update_temp_pixbuf()

	def on_horizontal_clicked(self, *args):
		self.flip_h = not self.flip_h
		self.update_temp_pixbuf()

	def on_tool_selected(self, *args):
		self.flip_selection = (self.window.hijacker_id is not None)
		self.flip_h = False
		self.flip_v = False
		self.update_temp_pixbuf()

	def update_temp_pixbuf(self):
		if self.flip_selection:
			if self.flip_h:
				self.get_image().set_temp_pixbuf(self.get_selection_pixbuf().flip(True))
			if self.flip_v:
				self.get_image().set_temp_pixbuf(self.get_selection_pixbuf().flip(False))
		else:
			if self.flip_h:
				self.get_image().set_temp_pixbuf(self.get_main_pixbuf().flip(True))
			if self.flip_v:
				self.get_image().set_temp_pixbuf(self.get_main_pixbuf().flip(False))

	def on_apply(self, *args):
		if self.flip_selection:
			if self.flip_h:
				self.get_image().set_selection_pixbuf(self.get_selection_pixbuf().flip(True))
			if self.flip_v:
				self.get_image().set_selection_pixbuf(self.get_selection_pixbuf().flip(False))
			self.window.get_selection_tool().on_confirm_hijacked_modif()
		else:
			if self.flip_h:
				self.get_image().set_main_pixbuf(self.get_main_pixbuf().flip(True))
			if self.flip_v:
				self.get_image().set_main_pixbuf(self.get_main_pixbuf().flip(False))
			self.window.force_selection_tool()



