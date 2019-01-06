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

		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/Drawing/modes/ui/rotate.ui')
		self.bottom_panel = builder.get_object('bottom-panel')

	def get_panel(self):
		return self.bottom_panel

	def get_edition_status(self):
		return _("Rotating the canvas")

	def on_mode_selected(self, *args):
		self.rotate_selection = args[0]
