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
		self.is_narrow = True # This is reducing the complexity of resizing,
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
		# If is_eos, hidable_widget is a box with paste/import, else it's the
		# "Open" button.
		self.hidable_widget = builder.get_object('hidable_widget')
		self.new_btn = builder.get_object('new_btn')
		self.main_menu_btn = builder.get_object('main_menu_btn')

		# Very high as a precaution, will be more precise later
		self.limit_size = 700

		builder.add_from_resource(UI_PATH + 'win-menus.ui')
		self.short_main_menu = builder.get_object('short-window-menu')
		self.long_main_menu = builder.get_object('long-window-menu')

		# This one is the default to be coherent with the default value of
		# self.is_narrow
		self.main_menu_btn.set_menu_model(self.long_main_menu)

		new_menu = builder.get_object('new-image-menu')
		self.new_btn.set_menu_model(new_menu)

		self.undo_btn = builder.get_object('undo_btn')
		# self.correct_btn = builder.get_object('correct_btn')
		self.redo_btn = builder.get_object('redo_btn')

	def init_adaptability(self):
		# Header bar width limit
		self.header_bar.show_all()
		widgets_width = self.save_label.get_preferred_width()[0] \
		               - self.save_icon.get_preferred_width()[0] \
		                 + self.new_btn.get_preferred_width()[0] \
		                + self.undo_btn.get_preferred_width()[0] \
		                + self.redo_btn.get_preferred_width()[0] \
		          + self.hidable_widget.get_preferred_width()[0]
		self.limit_size = 2.5 * widgets_width # 100% arbitrary
		# self.adapt_to_window_size() # XXX ferait sens mais ne semble pas efficace

	def adapt_to_window_size(self):
		can_expand = (self.header_bar.get_allocated_width() > self.limit_size)
		incoherent = (can_expand == self.is_narrow)
		if incoherent:
			self.set_compact(not self.is_narrow)

	def set_compact(self, state): # TODO state as an int
		if state:
			self.main_menu_btn.set_menu_model(self.long_main_menu)
		else:
			self.main_menu_btn.set_menu_model(self.short_main_menu)
		self.save_label.set_visible(not state)
		self.save_icon.set_visible(state)
		self.hidable_widget.set_visible(not state)
		self.new_btn.set_visible(not state)
		self.is_narrow = state

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

################################################################################

