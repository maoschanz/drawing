# custom_image.py
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

from gi.repository import Gtk, Gdk
from .utilities import utilities_add_unit_to_spinbtn

class DrawingCustomImageDialog(Gtk.Dialog):
	__gtype_name__ = 'DrawingCustomImageDialog'

	def __init__(self, appwindow):
		wants_csd = not ('ssd' in appwindow.decorations)
		super().__init__(use_header_bar=wants_csd, destroy_with_parent=True, \
		         transient_for=appwindow, title=_("New Image With Custom Size"))
		self._app_settings = appwindow._settings
		self._build_ui()
		self.set_default_size(450, 200)

	def _build_ui(self):
		self.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
		# Context: Create a new image
		btn = self.add_button(_("Create"), Gtk.ResponseType.OK)
		btn.get_style_context().add_class('suggested-action')

		ui_path = '/com/github/maoschanz/drawing/ui/'
		builder = Gtk.Builder.new_from_resource(ui_path + 'custom-image.ui')
		props_content_area = builder.get_object('props_content_area')
		self.get_content_area().add(props_content_area)

		self._width_btn = builder.get_object('spin_width')
		utilities_add_unit_to_spinbtn(self._width_btn, 4, 'px')
		default_w = self._app_settings.get_int('default-width')
		self._width_btn.set_value(default_w)

		self._height_btn = builder.get_object('spin_height')
		utilities_add_unit_to_spinbtn(self._height_btn, 4, 'px')
		default_h = self._app_settings.get_int('default-height')
		self._height_btn.set_value(default_h)

		self._color_btn = builder.get_object('color_btn')
		background_rgba = self._app_settings.get_strv('background-rgba')
		r = float(background_rgba[0])
		g = float(background_rgba[1])
		b = float(background_rgba[2])
		a = float(background_rgba[3])
		color = Gdk.RGBA(red=r, green=g, blue=b, alpha=a)
		self._color_btn.set_rgba(color)

		self._default_checkbtn = builder.get_object('default_checkbtn')

	############################################################################

	def get_values(self):
		"""Will be called from the main window if the user clicks on "Create",
		and returns the values set by the user."""
		width = self._width_btn.get_value_as_int()
		height = self._height_btn.get_value_as_int()
		rgba = self._color_btn.get_rgba()
		rgba = [str(rgba.red), str(rgba.green), str(rgba.blue), str(rgba.alpha)]
		if self._default_checkbtn.get_active():
			self._app_settings.set_int('default-width', width)
			self._app_settings.set_int('default-height', height)
			self._app_settings.set_strv('background-rgba', rgba)
		return width, height, rgba

	############################################################################
################################################################################
