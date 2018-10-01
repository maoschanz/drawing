# image.py
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
import cairo

# Cette classe représente une image et les méthodes qui lui sont associées.
# Cela concerne le chargement, l'exportation et le dimensionnement
# du GdkPixbuf.Pixbuf utilisé, mais aucune fonction d'édition ni de dessin.
class DrawCropDialog(Gtk.Dialog):
	__gtype_name__ = 'DrawCropDialog'

	def __init__(self, window, fn):
		super().__init__(use_header_bar=True, destroy_with_parent=True, parent=window)
		self.add_button(_("Apply"), Gtk.ResponseType.APPLY)
		self.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
		self.set_title(_("Crop image"))
		preview = Gtk.Layout()
		preview.connect('draw', self.on_draw)
		self.pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(fn, 500, 500, True)
		self.surface = Gdk.cairo_surface_create_from_pixbuf(self.pixbuf, 0, None)
		preview.set_size_request(self.surface.get_width(), self.surface.get_height())
		self.set_resizable(False)

		# TODO






		self.get_content_area().add(preview)
		self.show_all()

		result = self.run()
		if result == -10:
			print('apply') # TODO ?????

			# load normal de l'image avant une première coupe


			# x = ( coin gauche / width du pixbuf ) * width disponible
			# y = ( coin supérieur / height du pixbuf ) * height disponible
			# ...

			# window.resize_surface(self, x, y, width, height)

			window.initial_save()
		self.destroy()

	def on_draw(self, area, cairo_context):
		cairo_context.set_source_surface(self.surface, 0, 0)
		cairo_context.paint()
