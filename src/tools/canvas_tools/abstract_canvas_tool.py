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
		self.menu_id = 1
		self.centered_box = None
		self.needed_width_for_long = 0
		self.accept_selection = True

	def on_tool_selected(self, *args):
		super().on_tool_selected()
		self.apply_to_selection = self.selection_is_active()

	def give_back_control(self, preserve_selection):
		if not preserve_selection and self.selection_is_active():
			self.on_apply_temp_pixbuf_tool_operation()
			self.window.get_selection_tool().unselect_and_apply()
		super().give_back_control(preserve_selection)

	############################################################################

	def update_temp_pixbuf(self):
		operation = self.build_operation()
		self.do_tool_operation(operation)

	def on_apply_temp_pixbuf_tool_operation(self, *args):
		self.restore_pixbuf()
		operation = self.build_operation()
		self.apply_operation(operation)
		if self.apply_to_selection:
			self.window.force_selection()
		else:
			self.window.back_to_previous()

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
			self.get_selection().set_pixbuf(pixbuf, False, False)
			# XXX n'a pas l'air particulièrement efficace sur les scales successifs
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

	############################################################################

	def on_draw(self, area, cairo_context):
		pass # TODO FIXME pour l'instant pas d'overlay quand on modifie la sélection

	def get_deformed_surface(self, source_surface, p_xx, p_yx, p_xy, p_yy, p_x0, p_y0):
		source_w = source_surface.get_width()
		source_h = source_surface.get_height()
		# w = p_xx * source_w + p_xy * 0 + p_x0
		# h = p_yx * 0 + p_yy * source_h + p_y0
		normal_w = p_xx * source_w + p_xy * source_h + p_x0
		normal_h = p_yx * source_w + p_yy * source_h + p_y0
		# w = abs( p_xx * source_w ) + abs( p_xy * source_h ) + p_x0
		# h = abs( p_yx * source_w ) + abs( p_yy * source_h ) + p_y0

		# print('source_w, source_h', source_w, source_h)
		# print('normal_w, normal_h', normal_w, normal_h)
		# print('p_x0, p_y0', p_x0, p_y0 )

		# w = max(w, source_w) + p_x0
		# h = max(h, source_h) + p_y0

		w = max(normal_w, source_w + p_x0)
		h = max(normal_h, source_h + p_y0) # FIXME non toujours pas ?

		new_surface = cairo.ImageSurface(cairo.Format.ARGB32, int(w), int(h))
		cairo_context = cairo.Context(new_surface)
		# m = cairo.Matrix(xx=1.0, yx=0.0, xy=0.0, yy=1.0, x0=0.0, y0=0.0)
		m = cairo.Matrix(xx=p_xx, yx=p_yx, xy=p_xy, yy=p_yy, x0=p_x0, y0=p_y0)
		cairo_context.transform(m)
		cairo_context.set_source_surface(source_surface, 0, 0)
		# FIXME scroll and zoom ?
		cairo_context.paint()
		return new_surface

	############################################################################
################################################################################

