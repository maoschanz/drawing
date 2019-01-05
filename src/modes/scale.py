# scale.py
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

class ModeScale(ModeTemplate):
	__gtype_name__ = 'ModeScale'

	def __init__(self, window):
		super().__init__(window)
		self.keep_proportions = True

		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/Drawing/modes/ui/scale.ui')
		self.bottom_panel = builder.get_object('bottom-panel')

		self.height_btn = builder.get_object('height_btn')
		self.width_btn = builder.get_object('width_btn')

		self.add_mode_action_boolean('keep_proportions', True, self.set_keep_proportions)

	def get_panel(self):
		return self.bottom_panel

	def set_keep_proportions(self, *args):
		args[0].set_state(GLib.Variant.new_boolean(not args[0].get_state()))
		self.keep_proportions = args[0].get_state()
		if self.keep_proportions:
			self.proportion = self.get_width()/self.get_height()

	def on_apply_mode(self):
		w = self.get_width()
		h = self.get_height()
		if self.scale_selection:
			self.window.active_tool().scale_pixbuf_to(w, h)
		else:
			self.window.scale_pixbuf_to(w, h)

	def on_cancel_mode(self):
		print('cancel') # TODO

	def on_mode_selected(self, *args):
		self.scale_selection = args[0]
		if self.scale_selection:
			w = self.window.active_tool().selection_pixbuf.get_width()
			h = self.window.active_tool().selection_pixbuf.get_height()
		else:
			w = self.window.get_pixbuf_width()
			h = self.window.get_pixbuf_height()
		self.width_btn.set_value(w)
		self.height_btn.set_value(h)
		self.width_btn.connect('value-changed', self.on_width_changed)
		self.height_btn.connect('value-changed', self.on_height_changed)
		self.proportion = self.get_width()/self.get_height()

	def on_width_changed(self, *args):
		if self.keep_proportions:
			if self.proportion != self.get_width()/self.get_height():
				self.height_btn.set_value(self.get_width()/self.proportion)

	def on_height_changed(self, *args):
		if self.keep_proportions:
			if self.proportion != self.get_width()/self.get_height():
				self.width_btn.set_value(self.get_height()*self.proportion)

	def get_width(self):
		return self.width_btn.get_value_as_int()

	def get_height(self):
		return self.height_btn.get_value_as_int()

