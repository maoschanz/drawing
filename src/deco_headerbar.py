# headerbar.py
#
# Copyright 2018-2020 Romain F. T.
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
from .decorations_manager import DrawingDecorationsManager

class DrawingAdaptativeHeaderBar(DrawingDecorationsManager):
	__gtype_name__ = 'DrawingAdaptativeHeaderBar'

	def __init__(self, is_eos, window):
		super().__init__(window, False)
		self._is_narrow = True # This is reducing the complexity of resizing,
		# but its main goal is to avoid a GTK minor bug where the initial
		# bunch of configure-event signals was sent to soon.

		# Build the window's headerbar. If "is_eos" is true, the headerbar will
		# follow elementaryOS guidelines, else it will follow GNOME guidelines.
		if is_eos:
			resource_path = self.UI_PATH + 'headerbar-eos.ui'
		else:
			resource_path = self.UI_PATH + 'headerbar.ui'
		builder = Gtk.Builder.new_from_resource(resource_path)
		self._widget = builder.get_object('header_bar')
		window.set_titlebar(self._widget)

		# Code differences are kept minimal between the 2 cases: widgets will
		# share similar names in order to both work with the same method
		# updating widgets' visibility when resizing.
		self._save_label = builder.get_object('save_label')
		self._save_icon = builder.get_object('save_icon')
		# If is_eos, hidable_widget is a box with paste/import, else it's the
		# "Open" button.
		self._hidable_widget = builder.get_object('hidable_widget')
		self._new_btn = builder.get_object('new_btn')
		self._main_menu_btn = builder.get_object('main_menu_btn')

		# Quite high as a precaution, will be more precise later
		self._limit_size = 700

		builder.add_from_resource(self.UI_PATH + 'win-menus.ui')
		self._short_primary_menu = builder.get_object('short-window-menu')
		self._long_primary_menu = builder.get_object('long-window-menu')

		# This one is the default to be coherent with the default value of
		# self._is_narrow
		self._main_menu_btn.set_menu_model(self._long_primary_menu)

		new_menu = builder.get_object('new-image-menu')
		self._new_btn.set_menu_model(new_menu)

		self._undo_btn = builder.get_object('undo_btn')
		self._redo_btn = builder.get_object('redo_btn')

	def remove_from_ui(self):
		return False

	############################################################################

	def set_titles(self, title_label, subtitle_label):
		super().set_titles(title_label, subtitle_label)
		self._widget.set_title(title_label)
		self._widget.set_subtitle(subtitle_label)

	def set_undo_label(self, label):
		if label is None:
			self._undo_btn.set_tooltip_text(_("Undo"))
		else:
			self._undo_btn.set_tooltip_text(_("Undo %s") % label)

	def set_redo_label(self, label):
		if label is None:
			self._redo_btn.set_tooltip_text(_("Redo"))
		else:
			self._redo_btn.set_tooltip_text(_("Redo %s") % label)

	############################################################################
	# Adaptability #############################################################

	def init_adaptability(self):
		# Header bar width limit
		self._widget.show_all()
		widgets_width = self._save_label.get_preferred_width()[0] \
		               - self._save_icon.get_preferred_width()[0] \
		                 + self._new_btn.get_preferred_width()[0] \
		                + self._undo_btn.get_preferred_width()[0] \
		                + self._redo_btn.get_preferred_width()[0] \
		          + self._hidable_widget.get_preferred_width()[0]
		self._limit_size = 2.5 * widgets_width # 100% arbitrary

	def adapt_to_window_size(self):
		can_expand = (self._widget.get_allocated_width() > self._limit_size)
		incoherent = (can_expand == self._is_narrow)
		if incoherent:
			self.set_compact(not self._is_narrow)

	def set_compact(self, state):
		"""Set the compactness of the headerbar: if the parameter is True, wide
		widgets will be hidden in favor of narrow ones. Else, the opposite."""
		# XXX Instead of a boolean, `state` could be an integer, which would be
		# far more complex to handle, but would allow thinner granularity.
		if state:
			self._main_menu_btn.set_menu_model(self._long_primary_menu)
		else:
			self._main_menu_btn.set_menu_model(self._short_primary_menu)
		self._save_label.set_visible(not state)
		self._save_icon.set_visible(state)
		self._hidable_widget.set_visible(not state)
		self._new_btn.set_visible(not state)
		self._is_narrow = state

	############################################################################
################################################################################

