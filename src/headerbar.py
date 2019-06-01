# headerbar.py
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

UI_PATH = '/com/github/maoschanz/drawing/ui/'

class DrawingAdaptativeHeaderBar():
	__gtype_name__ = 'DrawingAdaptativeHeaderBar'

	def __init__(self, is_eos):
		self.is_short = True # This is reducing the complexity of resizing,
		# but its main goal is to avoid a GTK minor bug where the initial
		# bunch of configure-event signals was sent to soon, so the popover
		# was displayed a parallel universe when running the app on Wayland.
		if is_eos:
			builder = Gtk.Builder.new_from_resource(UI_PATH + 'headerbar_eos.ui')
		else:
			builder = Gtk.Builder.new_from_resource(UI_PATH + 'headerbar.ui')

		# Composition over inheritance
		self.header_bar = builder.get_object('header_bar')

		# Code differences are kept minimal between the 2 cases: widgets will
		# share similar names in order to both work with the same method
		# updating widgets' visibility when resizing.
		self.save_label = builder.get_object('save_label')
		self.save_icon = builder.get_object('save_icon')
		self.add_btn = builder.get_object('add_btn')
		self.main_menu_btn = builder.get_object('main_menu_btn')

		# Very high as a precaution, will be more precise later
		self.limit_size = 700

		builder.add_from_resource(UI_PATH + 'win-menus.ui')
		self.short_main_menu = builder.get_object('short-window-menu')
		self.long_main_menu = builder.get_object('long-window-menu')

		# This one is the default to be coherent with the default value of
		# self.is_short
		self.main_menu_btn.set_menu_model(self.long_main_menu)

		if is_eos:
			new_btn = builder.get_object('new_btn')
			add_menu = builder.get_object('new-image-menu')
			new_btn.set_menu_model(add_menu)
		else:
			add_menu = builder.get_object('add-menu')
			self.add_btn.set_menu_model(add_menu)

		self.undo_btn = builder.get_object('undo_btn')
		# self.correct_btn = builder.get_object('correct_btn')
		self.redo_btn = builder.get_object('redo_btn')

	def init_adaptability(self):
		# Header bar width limit
		self.header_bar.show_all()
		widgets_width = self.save_label.get_preferred_width()[0] \
			+ self.save_icon.get_preferred_width()[0] \
			+ self.add_btn.get_preferred_width()[0]
		self.limit_size = 3 * widgets_width # 100% arbitrary

	def adapt_to_window_size(self):
		if self.header_bar.get_allocated_width() < self.limit_size:
			if not self.is_short:
				self.is_short = True
				self.compact(True)
				self.main_menu_btn.set_menu_model(self.long_main_menu)
		else:
			if self.is_short:
				self.is_short = False
				self.compact(False)
				self.main_menu_btn.set_menu_model(self.short_main_menu)

	def compact(self, state):
		self.save_label.set_visible(not state)
		self.save_icon.set_visible(state)
		self.add_btn.set_visible(not state)

	def set_undo_label(self, label):
		if label is None:
			self.undo_btn.set_tooltip_text(_("Undo"))
		else:
			self.undo_btn.set_tooltip_text(_("Undo %s") % label)


	def set_redo_label(self, label):
		if label is None:
			self.redo_btn.set_tooltip_text(_("Redo"))
		else:
			self.redo_btn.set_tooltip_text(_("Redo %s") % label)



