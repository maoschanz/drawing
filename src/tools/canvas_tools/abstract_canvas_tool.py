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

	implements_panel = True

	def __init__(self, tool_id, label, icon_name, window, is_hidden, **kwargs):
		super().__init__(tool_id, label, icon_name, window, is_hidden)
		# TODO

	# def adapt_to_window_size(self):
	# 	available_width = self.window.bottom_panel_box.get_allocated_width()
	# 	if self.centered_box.get_orientation() == Gtk.Orientation.HORIZONTAL:
	# 		self.needed_width_for_long = self.centered_box.get_preferred_width()[0] + \
	# 			self.cancel_btn.get_allocated_width() + \
	# 			self.apply_btn.get_allocated_width()
	# 	if self.needed_width_for_long > 0.8 * available_width:
	# 		self.centered_box.set_orientation(Gtk.Orientation.VERTICAL)
	# 	else:
	# 		self.centered_box.set_orientation(Gtk.Orientation.HORIZONTAL)

	# def on_tool_selected(self, *args):
	# 	self.apply_to_selection = (self.window.hijacker_id is not None)
	# 	self._x = 0
	# 	self._y = 0
	# 	if self.apply_to_selection:
	# 		self.init_if_selection()
	# 	else:
	# 		self.init_if_main()

	# def update_temp_pixbuf(self):
	# 	operation = self.build_operation()
	# 	self.do_tool_operation(operation)



	def finish_temp_pixbuf_tool_operation(self, is_selection): # TODO mettre ça dans utilities ?
		cairo_context = cairo.Context(self.get_surface())
		if is_selection:
			cairo_context.set_source_surface(self.get_surface(), 0, 0)
			cairo_context.paint()
			self.get_image().delete_former_selection()
			Gdk.cairo_set_source_pixbuf(cairo_context, \
				self.get_image().get_temp_pixbuf(), \
				self.get_image().selection_x, \
				self.get_image().selection_y)
			cairo_context.paint()
		else:
			cairo_context.set_operator(cairo.Operator.CLEAR)
			cairo_context.paint()
			cairo_context.set_operator(cairo.Operator.OVER)
			Gdk.cairo_set_source_pixbuf(cairo_context, \
				self.get_image().get_temp_pixbuf(), \
				-1 * self.get_image().scroll_x, -1 * self.get_image().scroll_y)
			cairo_context.paint()
		self.non_destructive_show_modif()

	def on_apply_temp_pixbuf_tool_operation(self, *args):
		self.restore_pixbuf()
		operation = self.build_operation()
		if self.apply_to_selection:
			self.do_tool_operation(operation)
			self.get_image().selection_pixbuf = self.get_image().get_temp_pixbuf().copy()
			self.window.get_selection_tool().on_confirm_hijacked_modif()
		else:
			operation['is_preview'] = False
			self.apply_operation(operation)
			self.window.force_selection_tool()
