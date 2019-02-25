# pixbuf.py TODO
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

from gi.repository import Gtk, Gdk, GdkPixbuf
import cairo

class DrawingPixbuf():
	__gtype_name__ = 'DrawingPixbuf'

	def __init__(self):
		self._pixbuf = GdkPixbuf.Pixbuf(GdkPixbuf.Colorspace.RGB, True, 8, 1, 1)
		# TODO l'idée serait de faire des setters et des getters ici, ce qui serait orienté objet
		# ainsi que des méthodes plus simples pour redimensionner ou cropper ou pivoter.
		# la contrepartie serait que les tools auraient chacun le leur (si ils le souhaitent)
		# et on les "réinitialiserait" à une petite taille quand on quittera l'outil.
		# faisons ça plus tard ?

		# extension ou wrapper ??


