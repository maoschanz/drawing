# properties.py
#
# Copyright 2018-2022 Romain F. T.
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

from gi.repository import Gtk, GdkPixbuf, Pango

class DrPropertiesDialog(Gtk.Dialog):
	__gtype_name__ = 'DrPropertiesDialog'

	units_dict = {
		'px': _("%s px"),
		'cm': _("%s cm"),
		'in': _("%s in")
	}

	def __init__(self, parent_window, image):
		wants_csd = 'h' in parent_window.deco_layout
		super().__init__(use_header_bar=wants_csd, \
		                 destroy_with_parent=True, \
		                 transient_for=parent_window, \
		                 title=_("Image properties"))
		self._image = image
		self._build_ui()
		if wants_csd:
			subtitle = self._image.get_filename_for_display()
			self.get_titlebar().set_subtitle(subtitle)
			# put stackswitcher [Image|Metadata] as title_widget instead
		self.set_default_size(400, 150)
		self.show()

	def _build_ui(self):
		"""Fill the dialog with labels displaying correct information."""
		ui_file_path = '/com/github/maoschanz/drawing/ui/properties.ui'
		builder = Gtk.Builder.new_from_resource(ui_file_path)
		self.get_content_area().add(builder.get_object('main_widget'))
		self._grid = builder.get_object('image_props_grid')

		# Size (and size unit) #################################################

		self.label_width = builder.get_object('label_width')
		self.label_height = builder.get_object('label_height')

		self.unit = 'px'
		btn_px = builder.get_object('units_pixels')
		btn_in = builder.get_object('units_inches')
		btn_cm = builder.get_object('units_cm')
		btn_in.join_group(btn_px)
		btn_cm.join_group(btn_px)
		btn_px.connect('toggled', self._set_unit, 'px')
		btn_cm.connect('toggled', self._set_unit, 'cm')
		btn_in.connect('toggled', self._set_unit, 'in')

		self._set_size_labels()

		# Path, format and colorspace ##########################################

		if self._image.gfile is None:
			label_path = _("Unsaved file")
			label_file_format = _("Unsaved file")
		else:
			label_path = self._image.get_file_path()
			(pb_format, w, h) = GdkPixbuf.Pixbuf.get_file_info(label_path)
			label_file_format = pb_format.get_name()

		# Context: the path of the edited file
		self._add_grid_row(0, _("Path"), label_path)
		# Context: the file format of the edited file
		self._add_grid_row(1, _("Format"), label_file_format)
		self._add_grid_row(2, _("Colorspace"), self._set_colorspace_label())
		# TODO display both the colorspace of the file and of the surface, with
		# a warning if there might be a loss of data

	def _add_grid_row(self, index, key, value):
		"""Adds a row 2 labels (a key and a value) to the dialog's main grid."""
		key_label = Gtk.Label(label=key, halign=Gtk.Align.END, visible=True)
		self._grid.attach(key_label, 0, index, 1, 1)
		value_label = Gtk.Label(label=value, halign=Gtk.Align.START, \
		                 wrap=True, wrap_mode=Pango.WrapMode.CHAR, visible=True)
		value_label.get_style_context().add_class('dim-label')
		self._grid.attach(value_label, 1, index, 2, 1)

	def _set_colorspace_label(self):
		# Useless, it will always return "ARGB32"
		enum = {
			0: "ARGB32",
			1: "RGB24",
			2: "A8",
			3: "A1",
			4: "RGB16_565",
			5: "RGB30",
		}
		cairo_format = self._image.get_surface().get_format()
		# Context: an invalid colorspace format
		colorspace_text = enum.get(cairo_format, _("Invalid format"))
		return colorspace_text

	############################################################################

	def _set_size_labels(self):
		"""Set the labels for picture width and height according to the selected
		unit (px, cm or in)."""
		# TODO contrast this size with the size of the saved file
		px_width = self._image.get_pixbuf_width()
		px_height = self._image.get_pixbuf_height()
		if self.unit == 'in':
			width = round(px_width/96.0, 2)
			height = round(px_height/96.0, 2)
		elif self.unit == 'cm':
			width = round(px_width/37.795275591, 2)
			height = round(px_height/37.795275591, 2)
		else:
			width = px_width
			height = px_height
		self.label_width.set_label(self.units_dict[self.unit] % str(width))
		self.label_height.set_label(self.units_dict[self.unit] % str(height))

	def _set_unit(self, *args):
		self.unit = args[1]
		self._set_size_labels()

	############################################################################
################################################################################

# TODO pixbuf.get_options() ⇒
# * The PNG loader provides the tEXt ancillary chunk (http://www.libpng.org/pub/png/spec/1.2/PNG-Chunks.html 4.2.3) key/value pairs as options :

# Title            Short (one line) title or caption for image
# Author           Name of image's creator
# Description      Description of image (possibly long)
# Copyright        Copyright notice
# Creation Time    Time of original image creation
# Software         Software used to create the image
# Disclaimer       Legal disclaimer
# Warning          Warning of nature of content
# Source           Device used to create the image
# Comment          Miscellaneous comment; conversion from GIF comment

# * the TIFF and JPEG loaders return an “orientation” option string that corresponds to the embedded TIFF/Exif orientation tag (if present).
# * the TIFF loader sets the “multipage” option string to “yes” when a multi-page TIFF is loaded.
# * the JPEG and PNG loaders set “x-dpi” and “y-dpi” if the file contains image density information in dots per inch.
# * the JPEG loader sets the “comment” option with the comment EXIF tag.

