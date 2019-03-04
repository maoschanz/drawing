# message_dialog.py
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

from gi.repository import Gtk

class DrawingMessageDialog(Gtk.MessageDialog):
	__gtype_name__ = 'DrawingMessageDialog'

	def __init__(self, window, **kwargs):
		super().__init__(modal=True, title=_("Drawing"), transient_for=window, **kwargs)
		self.set_resizable(True)
		if window.get_allocated_width() < 500:
			self.get_action_area().set_orientation(Gtk.Orientation.VERTICAL)
			self.set_default_size(350, -1)

	def set_actions(self, labels):
		i = 1
		for action_label in labels:
			self.add_button(action_label, i)
			i = i+1

	def add_string(self, string):
		label = Gtk.Label(label=string, wrap=True)
		self.get_message_area().add(label)

	def add_widget(self, widget):
		self.get_content_area().add(widget)
