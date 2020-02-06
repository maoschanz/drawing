# properties.py
#
# Copyright 2018-2020 Romain F. T.
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

from gi.repository import Gtk, GdkPixbuf

class DrPropertiesDialog(Gtk.Dialog):
	__gtype_name__ = 'DrPropertiesDialog'

	def __init__(self, window, image):
		wants_csd = 'h' in window.deco_layout
		super().__init__(use_header_bar=wants_csd, destroy_with_parent=True, \
		                      transient_for=window, title=_("Image properties"))
		self._image = image
		self.build_ui()
		if wants_csd:
			subtitle = self._image.get_filename_for_display()
			self.get_titlebar().set_subtitle(subtitle)
		self.set_default_size(350, 200)
		self.show()

	def build_ui(self):
		"""Fill the dialog with labels displaying correct informations."""
		ui_path = '/com/github/maoschanz/drawing/ui/'
		builder = Gtk.Builder.new_from_resource(ui_path + 'properties.ui')
		props_content_area = builder.get_object('props_content_area')
		self.get_content_area().add(props_content_area)

		# Path and format ######################################################

		label_path = builder.get_object('label_path')
		label_format_file = builder.get_object('label_file_format')

		if self._image.gfile is not None:
			file_path = self._image.get_file_path()
			label_path.set_label(file_path)
			(pb_format, w, h) = GdkPixbuf.Pixbuf.get_file_info(file_path)
			label_format_file.set_label(pb_format.get_name())

		# Colorspace ###########################################################

		self.label_colorspace = builder.get_object('label_surface_colorspace')
		self.set_colorspace_label()

		# Size (and size unit) #################################################

		self.label_width = builder.get_object('label_width')
		self.label_height = builder.get_object('label_height')

		self.unit = ' px'
		btn_px = builder.get_object('units_pixels')
		btn_in = builder.get_object('units_inches')
		btn_cm = builder.get_object('units_cm')
		btn_in.join_group(btn_px)
		btn_cm.join_group(btn_px)
		# TODO translatable units
		btn_px.connect('toggled', self.set_unit, ' px')
		btn_cm.connect('toggled', self.set_unit, ' cm')
		btn_in.connect('toggled', self.set_unit, ' in')

		self.set_size_labels()

	def set_colorspace_label(self):
		enum = {
			0: 'ARGB32',
			1: 'RGB24',
			2: 'A8',
			3: 'A1',
			4: 'RGB16_565',
			5: 'RGB30',
		}
		cairo_format = self._image.get_surface().get_format()
		colorspace_text = enum.get(cairo_format, _("Invalid format"))
		self.label_colorspace.set_label(colorspace_text)
		return colorspace_text

	def set_size_labels(self):
		"""Set the labels for picture width and height according to the selected
		unit (px, cm or in)."""
		px_width = self._image.get_pixbuf_width()
		px_height = self._image.get_pixbuf_height()
		if self.unit == ' in':
			width = round(px_width/96.0, 2)
			height = round(px_height/96.0, 2)
		elif self.unit == ' cm':
			width = round(px_width/37.795275591, 2)
			height = round(px_height/37.795275591, 2)
		else:
			width = px_width
			height = px_height
		self.label_width.set_label(str(width) + self.unit)
		self.label_height.set_label(str(height) + self.unit)

	def set_unit(self, *args):
		self.unit = args[1]
		self.set_size_labels()

	############################################################################
################################################################################
