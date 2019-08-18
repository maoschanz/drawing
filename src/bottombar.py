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
		self.is_narrow = True
		self.widgets_narrow = []
		self.widgets_wide = []
		# TODO ? c'est tout ?

	def build_ui(self, end_of_path):
		builder = Gtk.Builder.new_from_resource(RESOURCE_PATH + end_of_path)
		self.action_bar = builder.get_object('bottom-panel')
		return builder # for implementations-specific widgets

	def build_options_menu(self, widget, model, label):
		pass

	def update_for_new_tool(self, tool): # and the menu? TODO
		pass

	def get_minimap_btn(self):
		pass

	def set_minimap_label(self, label):
		pass

	def init_adaptability(self):
		self.action_bar.show_all()
		long_size = 0
		for w in self.widgets_wide:
			print(w.get_preferred_width())
		# widgets_width = self.save_label.get_preferred_width()[0] \
		#                - self.save_icon.get_preferred_width()[0] \
		#                  + self.new_btn.get_preferred_width()[0] \
		#                 + self.undo_btn.get_preferred_width()[0] \
		#                 + self.redo_btn.get_preferred_width()[0] \
		#           + self.hidable_widget.get_preferred_width()[0]
		# self.limit_size = 2.5 * widgets_width # 100% arbitrary

	def adapt_to_window_size(self):
		can_expand = (self.action_bar.get_allocated_width() > self.limit_size)
		incoherent = (can_expand == self.is_narrow)
		if incoherent:
			self.set_compact(not self.is_narrow)

	def set_compact(self, state): # TODO state as an int
		# if state:
		# 	self.main_menu_btn.set_menu_model(self.long_main_menu)
		# else:
		# 	self.main_menu_btn.set_menu_model(self.short_main_menu)
		# self.save_label.set_visible(not state)
		# self.save_icon.set_visible(state)
		# self.hidable_widget.set_visible(not state)
		# self.new_btn.set_visible(not state)
		# self.is_narrow = state
		return

################################################################################

