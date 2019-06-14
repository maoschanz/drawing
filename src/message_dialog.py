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
		super().__init__(modal=True, transient_for=window, **kwargs)
		self.set_resizable(True)
		self.set_default_size(350, -1)

		# The dialog has already a default empty label, with methods around it,
		# but i don't care i'll add my widgets myself later.
		self.get_message_area().get_children()[0].destroy()

		if window.get_allocated_width() < 500:
			self.get_action_area().set_orientation(Gtk.Orientation.VERTICAL)
			self.should_wrap = True
		else:
			# Wrappable labels bother the height allocation, so they shouldn't
			# be used if it's not required
			self.should_wrap = False

	def set_actions(self, actions):
		for action in actions:
			# [label, style class, should be the default action, response id]
			btn = self.add_button(action[0], action[3])
			if action[1] is not None:
				btn.get_style_context().add_class(action[1])
			if action[2]:
				btn.grab_default()

	def add_string(self, string):
		label = Gtk.Label(label=string, wrap=self.should_wrap)
		self.get_message_area().add(label)
		self.get_message_area().show_all()

	def add_widget(self, widget):
		self.get_content_area().add(widget)
		self.get_content_area().show_all()

