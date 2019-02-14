# tool_saturate.py # XXX
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

class ToolSaturate(ToolTemplate):
	__gtype_name__ = 'ToolSaturate'

	implements_panel = True

	def __init__(self, window):
		super().__init__('saturate', _("Saturate"), 'weather-fog-symbolic', window)
		self.need_temp_pixbuf = True

		self.add_tool_action_simple('saturate_apply', self.on_apply)

		self.saturate_selection = False

		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/Drawing/tools/ui/tool_saturate.ui')
		self.bottom_panel = builder.get_object('bottom-panel')

		self.saturation_btn = builder.get_object('sat_btn')
		self.saturation_btn.connect('value-changed', self.on_sat_changed)

		self.window.bottom_panel_box.add(self.bottom_panel)

	def get_panel(self):
		return self.bottom_panel

	def on_tool_selected(self, *args):
		self.saturate_selection = (self.window.hijacker_id is not None)
		self.saturation_btn.set_value(100.0)
		self.update_temp_pixbuf()

	def update_temp_pixbuf(self):
		sat = self.get_saturation()
		if self.saturate_selection:
			pixbuf = self.get_selection_pixbuf()
		else:
			pixbuf = self.get_main_pixbuf()
		self.get_image().set_temp_pixbuf(pixbuf.saturate_and_pixelate(pixbuf, sat, False))

	def on_apply(self, *args):
		sat = self.get_saturation()
		print(sat)
		if self.saturate_selection:
			selection_pixbuf = self.get_selection_pixbuf()
			self.get_image().set_selection_pixbuf(selection_pixbuf.saturate_and_pixelate(selection_pixbuf, sat, False))
			self.window.former_tool().on_confirm_hijacked_modif()
		else:
			main_pixbuf = self.get_main_pixbuf()
			self.get_image().set_main_pixbuf(main_pixbuf.saturate_and_pixelate(main_pixbuf, sat, False))
			self.window.back_to_former_tool()

	def get_saturation(self):
		return self.saturation_btn.get_value()/100

	def on_sat_changed(self, *args):
		# self.update_temp_pixbuf() # FIXME
		pass # TODO
