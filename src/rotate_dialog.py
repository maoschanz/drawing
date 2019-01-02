# scale_dialog.py
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

from gi.repository import Gtk, Gdk, Gio, GdkPixbuf
from .gi_composites import GtkTemplate
import cairo

class DrawingRotateDialog(Gtk.Dialog):
	__gtype_name__ = 'DrawingRotateDialog'

	def __init__(self, window, w, h, is_selection):
		wants_csd = not ( 'ssd' in window._settings.get_string('decorations') )
		super().__init__(modal=True, use_header_bar=wants_csd, title=_("Rotate the picture"), transient_for=window)
		self._window = window
		self.is_selection = is_selection

		self.keep_proportions = True
		self.proportion = None

		self.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
		self.add_button(_("Apply"), Gtk.ResponseType.APPLY)
		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/Drawing/ui/rotate_dialog.ui')
		rotate_content_area = builder.get_object('rotate_content_area')
		self.get_content_area().add(rotate_content_area)

		self.show_all()
		self.set_resizable(False)

	def on_apply(self, *args):
		self.destroy()

	def on_cancel(self, *args):
		self.destroy()

