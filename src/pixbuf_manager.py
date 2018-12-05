# pixbuf_manager.py
#
# Copyright 2018 Romain F. T.
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

from gi.repository import Gtk, Gdk, Gio, GdkPixbuf, GLib
import cairo

# TODO
# gestion du pixbuf principal
# gestion du pixbuf de sélection
# gestion du presse-papier
# gestion de l'historique
class DrawingPixbufManager():
	main_pixbuf = None
	selection_pixbuf = None

	def __init__(self):
		pass

	def get_stable_pixbuf(self):
		pass

	def set_pixbuf_as_stable(self):
		pass

	def use_stable_pixbuf(self):
		pass

	def undo_operation(self):
		pass

	def cut_operation(self):
		pass

	def copy_operation(self):
		pass

	def paste_operation(self):
		pass

	def get_selection_pixbuf(self):
		pass


