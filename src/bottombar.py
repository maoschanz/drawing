# bottombar.py
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

from gi.repository import Gtk, Gdk

RESOURCE_PATH = '/com/github/maoschanz/drawing/'

class DrawingAdaptativeBottomBar():
	__gtype_name__ = 'DrawingAdaptativeBottomBar'
	# Abstract class

	def __init__(self):
		# Very high as a precaution, will be more precise later
		self.limit_size = 700
		self.is_narrow = False

	def build_ui(self, end_of_path):
		builder = Gtk.Builder.new_from_resource(RESOURCE_PATH + end_of_path)
		self.action_bar = builder.get_object('bottom-panel')
		self.cancel_btn = builder.get_object('cancel_btn') # may be None
		self.centered_box = builder.get_object('centered_box') # may be None
		self.apply_btn = builder.get_object('apply_btn') # may be None
		return builder # for implementations-specific widgets

	def build_options_menu(self, widget, model, label):
		pass

	def update_for_new_tool(self, tool): # and the menu? TODO
		pass

	def get_minimap_btn(self):
		pass

	def set_minimap_label(self, label):
		pass

	def toggle_options_menu(self):
		pass

	def init_adaptability(self):
		self.set_compact(False)
		self.action_bar.show_all()
		# + implementation-specific instructions

	def set_limit_size(self, temp_limit_size):
		self.limit_size = int(1.3 * temp_limit_size)
		self.set_compact(True)

	def adapt_to_window_size(self, allocated_width):
		can_expand = (allocated_width > self.limit_size)
		incoherent = (can_expand == self.is_narrow)
		if incoherent:
			self.set_compact(not self.is_narrow)

	def set_compact(self, state):
		self.is_narrow = state
		# + implementation-specific instructions

	############################################################################
################################################################################

