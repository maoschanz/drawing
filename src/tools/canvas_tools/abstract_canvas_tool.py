# abstract_canvas_tool.py
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

from gi.repository import Gtk, Gdk, GdkPixbuf
import cairo

from .abstract_tool import ToolTemplate

class AbstractCanvasTool(ToolTemplate):
	__gtype_name__ = 'AbstractCanvasTool'

	def __init__(self, tool_id, label, icon_name, window, **kwargs):
		super().__init__(tool_id, label, icon_name, window)
		self.implements_panel = True
		self.menu_id = 1
		self.centered_box = None
		self.needed_width_for_long = 0
		self.accept_selection = True

	def adapt_to_window_size(self, available_width):
		if self.centered_box is None:
			return
		if self.centered_box.get_orientation() == Gtk.Orientation.HORIZONTAL:
			self.needed_width_for_long = self.centered_box.get_preferred_width()[0] + \
				self.cancel_btn.get_allocated_width() + \
				self.apply_btn.get_allocated_width()
		if self.needed_width_for_long > 0.8 * available_width:
			self.centered_box.set_orientation(Gtk.Orientation.VERTICAL)
		else:
			self.centered_box.set_orientation(Gtk.Orientation.HORIZONTAL)

	def update_temp_pixbuf(self):
		operation = self.build_operation()
		self.do_tool_operation(operation)

	def on_apply_temp_pixbuf_tool_operation(self, *args):
		self.restore_pixbuf()
		operation = self.build_operation()
		self.apply_operation(operation)
		self.window.force_selection()

	def apply_operation(self, operation):
		operation['is_preview'] = False
		super().apply_operation(operation)
		self.get_image().reset_temp()

	def common_end_operation(self, is_preview, is_selection):
		if is_preview:
			self.temp_preview(is_selection)
		else:
			self.apply_temp(is_selection)

	def apply_temp(self, operation_is_selection):
		if operation_is_selection:
			self.get_selection().delete_temp()
			pixbuf = self.get_image().get_temp_pixbuf().copy() # XXX copy ??
			self.get_selection().set_pixbuf(pixbuf, False)
			# FIXME n'a pas l'air particulièrement efficace sur les scales successifs
		else:
			self.get_image().main_pixbuf = self.get_image().get_temp_pixbuf().copy()
			self.get_image().use_stable_pixbuf()

	def temp_preview(self, is_selection):
		"""Part of the previewing methods shared by all canvas tools."""
		cairo_context = cairo.Context(self.get_surface())
		if is_selection:
			cairo_context.set_source_surface(self.get_surface(), 0, 0)
			cairo_context.paint()
			self.get_selection().delete_temp()
			Gdk.cairo_set_source_pixbuf(cairo_context, \
			                            self.get_image().get_temp_pixbuf(), \
			                            self.get_selection().selection_x, \
			                            self.get_selection().selection_y)
			cairo_context.paint()
		else:
			cairo_context.set_operator(cairo.Operator.CLEAR)
			cairo_context.paint()
			cairo_context.set_operator(cairo.Operator.OVER)
			Gdk.cairo_set_source_pixbuf(cairo_context, \
			                           self.get_image().get_temp_pixbuf(), 0, 0)
			cairo_context.paint()
		self.get_image().update()

	def on_draw(self, area, cairo_context):
		pass # TODO FIXME pour l'instant pas d'overlay quand on modifie la sélection


