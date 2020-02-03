# deco_manager_toolbar.py
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
from .deco_manager_menubar import DrDecoManagerMenubar

class DrDecoManagerToolbar(DrDecoManagerMenubar):
	__gtype_name__ = 'DrDecoManagerToolbar'

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

		# Mandatory widget name, used for the `win.main_menu` action.
		self._main_menu_btn = builder.get_object('main_menu_btn')

		# XXX maybe later
		# self._undo_btn = builder.get_object('undo_btn')
		# self._redo_btn = builder.get_object('redo_btn')

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
			others_menu = builder.get_object('minimal-window-menu')
			self._main_menu_btn.set_menu_model(others_menu)

	def remove_from_ui(self):
		self._widget.destroy()
		return False

	############################################################################
################################################################################

