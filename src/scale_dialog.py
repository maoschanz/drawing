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

class DrawingScaleDialog(Gtk.Dialog):
	__gtype_name__ = 'DrawingScaleDialog'

	keep_proportions = True
	proportion = None

	def __init__(self, window, w, h, is_selection):
		wants_csd = not ( 'ssd' in window._settings.get_string('decorations') )
		super().__init__(modal=True, use_header_bar=wants_csd, title=_("Scale the picture"), transient_for=window)
		self._window = window
		self.is_selection = is_selection
		self.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
		self.add_button(_("Apply"), Gtk.ResponseType.APPLY)
		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/Drawing/ui/scale_dialog.ui')
		scale_content_area = builder.get_object('scale_content_area')
		self.get_content_area().add(scale_content_area)
		self.proportions_switch = builder.get_object('proportions_switch')
		self.height_btn = builder.get_object('height_btn')
		self.width_btn = builder.get_object('width_btn')
		self.set_resizable(False)

		self.width_btn.connect('value-changed', self.on_width_changed)
		self.height_btn.connect('value-changed', self.on_height_changed)
		self.proportions_switch.connect('notify::active', self.on_proportions_changed)
		self.width_btn.set_value(w)
		self.height_btn.set_value(h)

		self.proportions_switch.set_active(True)
		self.on_proportions_changed()

	def on_apply(self, *args):
		w = self.get_width()
		h = self.get_height()
		if self.is_selection:
			self._window._pixbuf_manager.selection_pixbuf = \
				self._window._pixbuf_manager.selection_pixbuf.scale_simple(w, h, GdkPixbuf.InterpType.TILES)
			self._window._pixbuf_manager.show_selection_rectangle()
		else:
			self._window._pixbuf_manager.main_pixbuf = \
				self._window._pixbuf_manager.main_pixbuf.scale_simple(w, h, GdkPixbuf.InterpType.TILES)
			self._window._pixbuf_manager.on_tool_finished()
		self.destroy()

	def on_cancel(self, *args):
		self.destroy()

	def on_draw(self, area, cairo_context):
		cairo_context.set_source_surface(self.surface, 0, 0)
		cairo_context.paint()

	def on_proportions_changed(self, *args):
		self.keep_proportions = self.proportions_switch.get_active()
		if self.keep_proportions:
			self.proportion = self.get_width()/self.get_height()

	def on_width_changed(self, *args):
		if self.keep_proportions and self.proportion is not None:
			if self.proportion != self.get_width()/self.get_height():
				self.height_btn.set_value(self.get_width()/self.proportion)

	def on_height_changed(self, *args):
		if self.keep_proportions and self.proportion is not None:
			if self.proportion != self.get_width()/self.get_height():
				self.width_btn.set_value(self.get_height()*self.proportion)

	def get_width(self):
		return self.width_btn.get_value_as_int()

	def get_height(self):
		return self.height_btn.get_value_as_int()

