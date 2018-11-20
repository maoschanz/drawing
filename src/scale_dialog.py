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

class DrawScaleDialog(Gtk.Dialog):
	__gtype_name__ = 'DrawScaleDialog'

	def __init__(self, window, o_width, o_height, forbid_growth):
		super().__init__(modal=True, use_header_bar=True, title=_("Scale the picture"), parent=window)
		self._window = window
		self.original_width = o_width
		self.original_height = o_height
		self.forbid_growth = forbid_growth
		self.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
		self.add_button(_("Apply"), Gtk.ResponseType.APPLY)
		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/Draw/ui/scale_dialog.ui')
		scale_content_area = builder.get_object('scale_content_area')
		self.get_content_area().add(scale_content_area)
		self.height_btn = builder.get_object('height_btn')
		self.width_btn = builder.get_object('width_btn')
		self.set_resizable(False)

		self.width_btn.connect('value-changed', self.on_width_changed)
		self.height_btn.connect('value-changed', self.on_height_changed)
		self._x = 0
		self._y = 0
		if self.forbid_growth:
			self.width_btn.set_range(1, self.original_width)
			self.height_btn.set_range(1, self.original_height)
		self.width_btn.set_value(self._window.pixbuf.get_width())
		self.height_btn.set_value(self._window.pixbuf.get_height())

	def on_apply(self, *args): # TODO
#		x = self._x
#		y = self._y
#		width = self.get_width()
#		height = self.get_height()

#		self._window.resize_surface(x, y, width, height)
#		self._window.initial_save()
		self.destroy()

	def on_cancel(self, *args):
		self.destroy()

	def on_draw(self, area, cairo_context):
		cairo_context.set_source_surface(self.surface, 0, 0)
		cairo_context.paint()

	def on_width_changed(self, *args):
		self.draw_overlay()

	def on_height_changed(self, *args):
		self.draw_overlay()

	def get_width(self):
		return self.width_btn.get_value_as_int()

	def get_height(self):
		return self.height_btn.get_value_as_int()

