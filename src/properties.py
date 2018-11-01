# properties.py
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

class DrawPropertiesDialog(Gtk.Dialog):
	__gtype_name__ = 'DrawPropertiesDialog'

	def __init__(self, window):
		super().__init__(use_header_bar=True, destroy_with_parent=True, parent=window)
		self.add_button(_("Apply"), Gtk.ResponseType.APPLY)
		self.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
		self.set_title(_("Image properties"))

		prop_grid = Gtk.Grid(column_spacing=25, row_spacing=15, margin=25, column_homogeneous=False)

		if window._file_path is not None:
			label_path = Gtk.Label(window._file_path, wrap=True)
			(pb_format, width, height) = GdkPixbuf.Pixbuf.get_file_info(window._file_path)
			label_format_file = Gtk.Label(pb_format.get_name())
		else:
			label_path = Gtk.Label(_("Unsaved file"))
			label_format_file = Gtk.Label(_("Unsaved file"))

		prop_grid.attach(Gtk.Label(_("Path")), 0, 0, 1, 1)
		label_path.get_style_context().add_class('dim-label')
		prop_grid.attach(label_path, 1, 0, 2, 1)

		prop_grid.attach(Gtk.Label(_("Format")), 0, 1, 1, 1)
		label_format_file.get_style_context().add_class('dim-label')
		prop_grid.attach(label_format_file, 1, 1, 1, 1)
		enum = {
			0: 'ARGB32',
			1: 'RGB24',
			2: 'A8',
			3: 'A1',
			4: 'RGB16_565',
			5: 'RGB30',
		}
		label_format_surface = Gtk.Label(enum.get(window._surface.get_format(), _("Invalid format")))
		label_format_surface.get_style_context().add_class('dim-label')
		prop_grid.attach(label_format_surface, 2, 1, 1, 1)

		prop_grid.attach(Gtk.Separator(), 0, 2, 3, 1)

		prop_grid.attach(Gtk.Label(_("Width")), 0, 3, 1, 1)
		width_btn = Gtk.SpinButton()
		width_btn.set_range(1, 4000)
		width_btn.set_increments(1, 1)
		width_btn.set_value(window._surface.get_width())
		prop_grid.attach(width_btn, 2, 3, 1, 1)

		prop_grid.attach(Gtk.Label(_("Height")), 0, 4, 1, 1)
		height_btn = Gtk.SpinButton()
		height_btn.set_range(1, 4000)
		height_btn.set_increments(1, 1)
		height_btn.set_value(window._surface.get_height())
		prop_grid.attach(height_btn, 2, 4, 1, 1)

		prop_grid.set_halign(Gtk.Align.CENTER)
		self.get_content_area().add(prop_grid)

		self.set_default_size(400, 100)

		self.show_all()
		result = self.run()
		if result == -10:
			window.resize_surface(0, 0, width_btn.get_value(), height_btn.get_value())
		self.destroy()
