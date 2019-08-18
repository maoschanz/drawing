# color_popover.py
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

from gi.repository import Gtk, Gdk
import cairo

class DrawingColorPopover(Gtk.Popover):
	__gtype_name__ = 'DrawingColorPopover'

	def __init__(self, btn, image, initial_rgba, **kwargs):
		super().__init__(**kwargs)

		builder = Gtk.Builder.new_from_resource( \
		                    '/com/github/maoschanz/drawing/ui/color_popover.ui')
		main_box = builder.get_object('main-box')
		self.add(main_box)
		btn.set_popover(self)
		self.btn_image = image

		r = float(initial_rgba[0])
		g = float(initial_rgba[1])
		b = float(initial_rgba[2])
		a = float(initial_rgba[3])
		initial_rgba = Gdk.RGBA(red=r, green=g, blue=b, alpha=a)

		self.color_widget = builder.get_object('color-widget')
		self.color_widget.set_rgba(initial_rgba)

		back_btn = builder.get_object('back-btn')
		self.editor_box = builder.get_object('editor-box')

		self.color_widget.connect('notify::rgba', self.set_color_btn)
		self.color_widget.connect('notify::show-editor', self.update_box)
		back_btn.connect('clicked', self.close_color_editor)

		self.update_box()
		self.set_color_btn()

	def setting_changed(self, show_editor):
		self.color_widget.props.show_editor = show_editor
		self.update_box()

	def close_color_editor(self, *args):
		self.color_widget.props.show_editor = False

	def update_box(self, *args):
		"""Update the visibility of navigation controls ('back to the palette'
		and 'always use this editor')."""
		self.editor_box.set_visible(self.color_widget.props.show_editor)

	def set_color_btn(self, *args):
		"""Update the 'rgba' property of the GtkColorWidget and its preview."""
		surface = cairo.ImageSurface(cairo.Format.ARGB32, 16, 16)
		cairo_context = cairo.Context(surface)
		rgba = self.color_widget.get_rgba()
		cairo_context.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)
		cairo_context.paint()
		self.btn_image.set_from_surface(surface)
