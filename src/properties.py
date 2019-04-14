# properties.py
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

from gi.repository import Gtk, Gdk, Gio, GdkPixbuf
import cairo

class DrawingPropertiesDialog(Gtk.Dialog):
	__gtype_name__ = 'DrawingPropertiesDialog'

	def __init__(self, window, image):
		wants_csd = not ('ssd' in window.decorations)
		super().__init__(use_header_bar=wants_csd, destroy_with_parent=True, \
			transient_for=window, title=_("Image properties"))
		self._image = image
		self.build_ui()
		self.set_default_size(350, 200)
		self.show()

	def build_ui(self):
		"""Fill the dialog with labels displaying correct informations."""
		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/drawing/ui/properties.ui')
		props_content_area = builder.get_object('props_content_area')
		self.get_content_area().add(props_content_area)

		# Alpha channel

		self.label_alpha_info = builder.get_object('label_alpha_info')

		self.toggle_alpha = builder.get_object('add_alpha_toggle')
		self.toggle_alpha.connect('toggled', self.set_alpha_widgets_visibility)

		self.add_alpha_button = builder.get_object('add_alpha_button')
		self.add_alpha_button.connect('clicked', self.add_alpha_to_image)

		# Path and format

		label_path = builder.get_object('label_path')
		label_format_file = builder.get_object('label_format_file')
		self.label_format_surface = builder.get_object('label_format_surface')

		if self._image.gfile is not None:
			label_path.set_label(self._image.get_file_path())
			(pb_format, width, height) = GdkPixbuf.Pixbuf.get_file_info( \
			                                        self._image.get_file_path())
			label_format_file.set_label(pb_format.get_name())

		self.set_format_label()

		# Size (and size unit)

		self.label_width = builder.get_object('label_width')
		self.label_height = builder.get_object('label_height')

		self.unit = ' px'
		btn_px = builder.get_object('units_pixels')
		btn_in = builder.get_object('units_inches')
		btn_cm = builder.get_object('units_cm')
		btn_in.join_group(btn_px)
		btn_cm.join_group(btn_px)
		btn_px.connect('toggled', self.set_unit, ' px')
		btn_cm.connect('toggled', self.set_unit, ' cm')
		btn_in.connect('toggled', self.set_unit, ' in')

		self.set_size_labels()

	def set_format_label(self):
		enum = {
			0: 'ARGB32',
			1: 'RGB24',
			2: 'A8',
			3: 'A1',
			4: 'RGB16_565',
			5: 'RGB30',
		}
		cairo_format = enum.get(self._image.get_surface().get_format(), _("Invalid format"))
		self.label_format_surface.set_label(cairo_format)
		if cairo_format is 'ARGB32':
			self.label_alpha_info.set_label( \
			            _("This surface format already supports transparency."))
		else:
			self.label_alpha_info.set_label( \
			          _("This surface format doesn't support transparency, " + \
			  "you can add an alpha channel, optionally by replacing a color."))
		return cairo_format

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

	def set_alpha_widgets_visibility(self, *args):
		visible = args[0].get_active()
		self.label_alpha_info.set_visible(visible)
		if (self.set_format_label() is not 'ARGB32') or (not visible):
			self.add_alpha_button.set_visible(visible)

	def set_unit(self, *args):
		self.unit = args[1]
		self.set_size_labels()

	def set_color_btn_sensitivity(self, *args):
		want_color = self.switch_alpha_color.get_active()
		self.button_alpha_color.set_sensitive(want_color)

	def add_alpha_to_image(self, *args): # XXX not retained by history ?
		self._image.main_pixbuf = self._image.main_pixbuf.add_alpha(False, 0, 0, 0)
		self._image.use_stable_pixbuf()
		self._image.queue_draw()
		self.set_format_label()
		self.add_alpha_button.set_visible(False)

