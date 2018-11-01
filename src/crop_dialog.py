# crop_dialog.py
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

# FIXME should be a dialog but i've no idea how to do a dialog with an UI file
@GtkTemplate(ui='/com/github/maoschanz/Draw/ui/crop_dialog.ui')
class DrawCropWindow(Gtk.Window):
	__gtype_name__ = 'DrawCropWindow'

	preview = GtkTemplate.Child()
	cancel_btn = GtkTemplate.Child()
	apply_btn = GtkTemplate.Child()
	width_btn = GtkTemplate.Child()
	height_btn = GtkTemplate.Child()

	def __init__(self, window, fn):
		super().__init__()
		self.init_template()
		self.preview.connect('draw', self.on_draw)
		self.pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(fn, 500, 500, True)
		self.surface = Gdk.cairo_surface_create_from_pixbuf(self.pixbuf, 0, None)
		self.preview.set_size_request(self.surface.get_width(), self.surface.get_height())
		self.set_resizable(False)

		self.apply_btn.connect('clicked', self.on_apply)
		self.cancel_btn.connect('clicked', self.on_cancel)

		self.width_btn.connect('value-changed', self.on_width_changed)
		self.height_btn.connect('value-changed', self.on_height_changed)

	def on_apply(self, *args):
		print('apply') # TODO

		# load normal de l'image avant une première coupe


		# x = ( coin gauche / width du pixbuf ) * width disponible
		# y = ( coin supérieur / height du pixbuf ) * height disponible
		# ...

		# window.resize_surface(self, x, y, width, height)

		window.initial_save()

	def on_cancel(self, *args):
		self.destroy()

	def on_draw(self, area, cairo_context):
		cairo_context.set_source_surface(self.surface, 0, 0)
		cairo_context.paint()

	def on_width_changed(self, *args):
		print(self.width_btn.get_value())

	def on_height_changed(self, *args):
		print(self.height_btn.get_value())      
