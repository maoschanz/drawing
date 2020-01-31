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

class DrawingDecoToolbar(DrawingDecorationsManager):
	__gtype_name__ = 'DrawingDecoToolbar'

	def __init__(self, is_symbolic, with_menubar, window):
		super().__init__(window, with_menubar)
		window.set_titlebar(None) # that's an arbitrary restriction
		if is_symbolic:
			resource_path = self.UI_PATH + 'toolbar-symbolic.ui'
		else:
			resource_path = self.UI_PATH + 'toolbar.ui'
		builder = Gtk.Builder.new_from_resource(resource_path)

		# Composition over inheritance
		self._widget = builder.get_object('toolbar')
		window.toolbar_box.pack_start(self._widget, True, True, 0)
		window.toolbar_box.show_all()

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

		# The toolbar has menus which need to be set manually
		builder.add_from_resource(self.UI_PATH + 'win-menus.ui')

		new_btn = builder.get_object('new_menu_btn')
		new_menu = Gtk.Menu.new_from_model(builder.get_object('new-image-menu'))
		new_btn.set_menu(new_menu)

		save_btn = builder.get_object('save_menu_btn')
		save_menu = Gtk.Menu.new_from_model(builder.get_object('save-section'))
		save_btn.set_menu(save_menu)

		if with_menubar:
			self._main_menu_btn.set_visible(False)
		else:
			others_menu = builder.get_object('toolbar-menu')
			self._main_menu_btn.set_menu_model(others_menu)

	def remove_from_ui(self):
		self._widget.destroy()
		return False

	############################################################################
################################################################################

