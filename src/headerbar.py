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

class DrawingAdaptativeHeaderBar():
	__gtype_name__ = 'DrawingAdaptativeHeaderBar'

	def __init__(self, window, is_eos):
		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/drawing/ui/headerbar.ui')
		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/drawing/ui/headerbar_eos.ui')
		 = builder.get_object('')
		 = builder.get_object('') # TODO
		 = builder.get_object('')
		 = builder.get_object('')

	def init_adaptability(self):
		pass

	def adapt_to_window_size(self):
		pass

	def compact(self, state):
		pass
