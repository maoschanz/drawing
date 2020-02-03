# deco_manager_menubar.py
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

class DrDecoManagerMenubar():
	__gtype_name__ = 'DrDecoManagerMenubar'
	UI_PATH = '/com/github/maoschanz/drawing/ui/'

	def __init__(self, window, use_menubar):
		window.set_show_menubar(use_menubar)
		self._window = window
		self._main_menu_btn = None
		if use_menubar:
			window.set_titlebar(None) # that's an arbitrary restriction

	def remove_from_ui(self):
		return False

	############################################################################

	def set_titles(self, title_label, subtitle_label):
		full_title = _("Drawing") + ' - ' + title_label + ' - ' + subtitle_label
		self._window.set_title(full_title)

	def toggle_menu(self):
		if self._main_menu_btn is not None:
			self._main_menu_btn.set_active(not self._main_menu_btn.get_active())

	def set_undo_label(self, label):
		pass

	def set_redo_label(self, label):
		pass

	############################################################################
	# Adaptability #############################################################

	def init_adaptability(self):
		pass

	def adapt_to_window_size(self):
		pass

	def set_compact(self, state):
		pass

	############################################################################
################################################################################

