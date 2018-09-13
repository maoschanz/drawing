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
class DrawImage():
    __gtype_name__ = 'DrawImage'

    def __init__(self, window):
        self._window = window
        self.pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 1000, 600) # 8 ??? les autres plantent

    def edit_properties(self, a, b):
        dialog = Gtk.Dialog(use_header_bar=True, destroy_with_parent=True, parent=self._window)
        dialog.add_button(_("Apply"), Gtk.ResponseType.APPLY)
        dialog.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
        dialog.set_title(_("Image properties"))

        prop_grid = Gtk.Grid(column_spacing=25, row_spacing=15, margin=25, column_homogeneous=False)

        if self._window._file_path is not None:
            label_path = Gtk.Label(self._window._file_path, wrap=True)
            (pb_format, width, height) = GdkPixbuf.Pixbuf.get_file_info(self._window._file_path)
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
        label_format_surface = Gtk.Label(enum.get(self._window._surface.get_format(), _("Invalid format")))
        label_format_surface.get_style_context().add_class('dim-label')
        prop_grid.attach(label_format_surface, 2, 1, 1, 1)

        prop_grid.attach(Gtk.Separator(), 0, 2, 3, 1)

        prop_grid.attach(Gtk.Label(_("Width")), 0, 3, 1, 1)
        width_btn = Gtk.SpinButton()
        width_btn.set_range(1, 4000)
        width_btn.set_increments(1, 1)
        width_btn.set_value(self._window._surface.get_width())
        prop_grid.attach(width_btn, 2, 3, 1, 1)

        prop_grid.attach(Gtk.Label(_("Height")), 0, 4, 1, 1)
        height_btn = Gtk.SpinButton()
        height_btn.set_range(1, 4000)
        height_btn.set_increments(1, 1)
        height_btn.set_value(self._window._surface.get_height())
        prop_grid.attach(height_btn, 2, 4, 1, 1)

        prop_grid.set_halign(Gtk.Align.CENTER)
        dialog.get_content_area().add(prop_grid)

        dialog.set_default_size(400, 100)

        dialog.show_all()
        result = dialog.run()
        if result == -10:

            # The GdkPixbuf.Pixbuf.copy_area method works only when expanding the size
            max_width = max(int(width_btn.get_value()), self._window._surface.get_width())
            max_height = max(int(height_btn.get_value()), self._window._surface.get_height())
            new_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, max_width, max_height)
            self.pixbuf.copy_area(0, 0, self._window._surface.get_width(), self._window._surface.get_height(), new_pixbuf, 0, 0)
            self.pixbuf = new_pixbuf

            # The cairo.Surface.map_to_image method works only when reducing the size
            self._window._surface = Gdk.cairo_surface_create_from_pixbuf(self.pixbuf, 0, None)
            self._window._surface = self._window._surface.map_to_image(cairo.RectangleInt(0, 0, \
                int(width_btn.get_value()), int(height_btn.get_value())))
            self.pixbuf = Gdk.pixbuf_get_from_surface(self._window._surface, 0, 0, \
                self._window._surface.get_width(), self._window._surface.get_height())

            self._window.drawing_area.set_size(int(width_btn.get_value()), int(height_btn.get_value()))
        dialog.destroy()

    def invoke_file_chooser(self):
        file_path = None
        file_chooser = Gtk.FileChooserDialog(_("Save as"), self._window,
            Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        response = file_chooser.run()
        if response == Gtk.ResponseType.OK:
            file_path = file_chooser.get_filename()
        file_chooser.destroy()
        return file_path

    def export_as_png(self, a, b):
        file_path = self.invoke_file_chooser()
        self._window.post_modification()
        self.pixbuf.savev(file_path, "png", [None], [])

    def export_as_jpeg(self, a, b):
        file_path = self.invoke_file_chooser()
        self._window.post_modification()
        self.pixbuf.savev(file_path, "jpeg", [None], [])

    def export_as_bmp(self, a, b):
        file_path = self.invoke_file_chooser()
        self._window.post_modification()
        self.pixbuf.savev(file_path, "bmp", [None], [])

    def load_self_file(self):
        self.pixbuf = GdkPixbuf.Pixbuf.new_from_file(self._window._file_path)
        self._window.header_bar.set_subtitle(self._window._file_path)
        self._window.pre_modification()