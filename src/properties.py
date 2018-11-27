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

from .crop_dialog import DrawCropDialog

class DrawPropertiesDialog(Gtk.Dialog):
	__gtype_name__ = 'DrawPropertiesDialog'

	def __init__(self, window):
		super().__init__(use_header_bar=True, destroy_with_parent=True, parent=window, title=_("Image properties"))
		self._window = window
		# self.add_button(_("Apply"), Gtk.ResponseType.APPLY)
		# self.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)

		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/Drawing/ui/properties_dialog.ui')
		props_content_area = builder.get_object('props_content_area')
		self.get_content_area().add(props_content_area)

		label_path = builder.get_object('label_path')
		label_format_file = builder.get_object('label_format_file')
		label_format_surface = builder.get_object('label_format_surface')
		label_width = builder.get_object('label_width')
		label_height = builder.get_object('label_height')

		if window._file_path is not None:
			label_path.set_label(window._file_path)
			(pb_format, width, height) = GdkPixbuf.Pixbuf.get_file_info(window._file_path)
			label_format_file.set_label(pb_format.get_name())

		enum = {
			0: 'ARGB32',
			1: 'RGB24',
			2: 'A8',
			3: 'A1',
			4: 'RGB16_565',
			5: 'RGB30',
		}
		label_format_surface.set_label(enum.get(window._surface.get_format(), _("Invalid format")))

		label_width.set_label(str(window._surface.get_width()) + ' px')
		label_height.set_label(str(window._surface.get_height()) + ' px')

		btn_crop = builder.get_object('btn_crop')
		btn_crop.connect('clicked', self.on_crop)

		btn_scale = builder.get_object('btn_scale')
		btn_scale.connect('clicked', self.on_scale)

		self.set_default_size(400, 100)
		self.show_all()

	def on_scale(self, b):
		self._window.action_scale()
	# TODO : update labels where size is written

	def on_crop(self, b):
		self._window.action_crop()
	# TODO : update labels where size is written
