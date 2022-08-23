# abstract_transform_tool.py
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

import cairo
from gi.repository import Gtk, Gdk, GdkPixbuf

from .abstract_tool import AbstractAbstractTool

class AbstractCanvasTool(AbstractAbstractTool):
	__gtype_name__ = 'AbstractCanvasTool'

	def __init__(self, tool_id, label, icon_name, window, **kwargs):
		super().__init__(tool_id, label, icon_name, window)
		self.menu_id = 1
		self.centered_box = None
		self.needed_width_for_long = 0
		self.accept_selection = True
		self.apply_to_selection = False
		self._directions = ''

		# Gdk.RGBA
		self._expansion_rgba = None

		# ugly ass lock so the 'cancel' button does actually cancel
		self._auto_apply_next = True

	def on_tool_selected(self, *args):
		super().on_tool_selected()
		self.apply_to_selection = self.selection_is_active()

	def update_actions_state(self, *args):
		# Changing this in on_tool_selected would be overridden by image.py
		super().update_actions_state()

		self.set_action_sensitivity('selection_delete', False)
		self.set_action_sensitivity('selection_cut', False)
		self.set_action_sensitivity('unselect', False)
		self.set_action_sensitivity('select_all', False)

		self.set_action_sensitivity('cancel_transform', True)
		self.set_action_sensitivity('apply_transform', True)

	def give_back_control(self, preserve_selection=True):
		if not preserve_selection and self.selection_is_active():
			self.window.get_selection_tool().unselect_and_apply()
		super().give_back_control(preserve_selection)

	def auto_apply(self, next_tool_id):
		if next_tool_id == self.id:
			return # avoid some weird recursive situations
		if not self._auto_apply_next:
			self._auto_apply_next = True
			return
		self.restore_pixbuf()
		operation = self.build_operation()
		self.apply_operation(operation)

	def _scroll_to_end(self, h_growth, v_growth):
		if h_growth > 0:
			if 'e' in self._directions:
				self.window.action_go_last()
		if v_growth > 0:
			if 's' in self._directions:
				self.window.action_go_bottom()
		self.get_image().fake_scrollbar_update()

	############################################################################

	def build_and_do_op(self):
		operation = self.build_operation()
		self.do_tool_operation(operation)

	def temp_preview(self, is_selection, local_dx, local_dy):
		"""Part of the previewing methods shared by all transform tools."""
		pixbuf = self.get_image().temp_pixbuf
		cairo_context = self.get_context()
		if is_selection:
			cairo_context.set_source_surface(self.get_surface(), 0, 0)
			cairo_context.paint()
			x = self.get_selection().selection_x + local_dx
			y = self.get_selection().selection_y + local_dy
			Gdk.cairo_set_source_pixbuf(cairo_context, pixbuf, x, y)
			cairo_context.paint()
		else:
			cairo_context.set_operator(cairo.Operator.SOURCE)
			Gdk.cairo_set_source_pixbuf(cairo_context, pixbuf, 0, 0)
			cairo_context.paint()
			cairo_context.set_operator(cairo.Operator.OVER)
		self.get_image().update()

	############################################################################

	def on_apply_transform_tool_operation(self):
		if self.apply_to_selection:
			self.window.force_selection()
		else:
			self.window.back_to_previous()
		# The operation itself will be applied by the `auto_apply` method

	def on_cancel_transform_tool_operation(self, *args):
		self._auto_apply_next = False
		self.on_apply_transform_tool_operation() # change the active tool

	def apply_operation(self, operation):
		operation['is_preview'] = False
		super().apply_operation(operation)
		self.get_image().reset_temp()

	def common_end_operation(self, op):
		if op['is_preview']:
			self.temp_preview(op['is_selection'], op['local_dx'], op['local_dy'])
		else:
			self.apply_temp(op['is_selection'], op['local_dx'], op['local_dy'])

	def apply_temp(self, operation_is_selection, ldx, ldy):
		new_pixbuf = self.get_image().temp_pixbuf.copy()
		if operation_is_selection:
			self.get_selection().update_from_transform_tool(new_pixbuf, ldx, ldy)
		else:
			self.get_image().set_main_pixbuf(new_pixbuf)
			self.get_image().use_stable_pixbuf()

	############################################################################
	# Direction of the cursor depending on its position ########################

	def _set_directions(self, event_x, event_y, n_sizes):
		"""Set the directions of the user's future operation for tools such as
		`scale` or `crop`.
		It returns a boolean telling whether or not the directions changed since
		the last call to this method."""
		w_left = n_sizes['wl']
		w_right = n_sizes['wr']
		h_top = n_sizes['ht']
		h_bottom = n_sizes['hb']
		# print("set_directions", w_left, w_right, h_top, h_bottom)
		directions = ''
		if event_y < h_top:
			directions += 'n'
		elif event_y > h_bottom:
			directions += 's'
		if event_x < w_left:
			directions += 'w'
		elif event_x > w_right:
			directions += 'e'

		if self._directions == directions:
			return False
		else:
			self._directions = directions
			return True

	def _set_cursor_name(self):
		"""Set the cursor name, depending on the previously set directions."""
		if self._directions == '':
			self.cursor_name = 'not-allowed'
		else:
			self.cursor_name = self._directions + '-resize'

	def set_directional_cursor(self, event_x, event_y, movable_center=False):
		"""Set the accurate cursor depending on the position of the pointer on
		the canvas."""
		n_sizes = self.get_image().get_nineths_sizes(self.apply_to_selection, \
		                                                       self._x, self._y)
		# if we're transforming the selection from its top and/or left, coords
		# to decide the direction depend on local deltas (self._x and self._y)
		if not self._set_directions(event_x, event_y, n_sizes):
			# directions haven't changed
			return
		if movable_center and self._directions == '':
			self.cursor_name = 'move'
		else:
			self._set_cursor_name()
		self.window.set_cursor(True)

	############################################################################

	def on_draw_above(self, area, cairo_context):
		pass

	def _draw_temp_pixbuf(self, cairo_context, x, y):
		pixbuf = self.get_image().temp_pixbuf
		Gdk.cairo_set_source_pixbuf(cairo_context, pixbuf, x, y)
		if self.get_image().is_zoomed_surface_sharp():
			cairo_context.get_source().set_filter(cairo.FILTER_NEAREST)
		cairo_context.paint()

	def get_resized_surface(self, source_surface, coefs):
		"""Generate a blank new surface whose size is enough to fit a cairo
		matrix transformation of `source_surface` using the coefficients in
		`coefs`. The method `get_deformed_surface` should be used next."""
		p_xx, p_yx, p_xy, p_yy, p_x0, p_y0 = coefs
		source_w = source_surface.get_width()
		source_h = source_surface.get_height()
		w = p_xx * source_w + p_xy * source_h + p_x0 * 2
		h = p_yx * source_w + p_yy * source_h + p_y0 * 2
		return cairo.ImageSurface(cairo.Format.ARGB32, int(w), int(h))

	def get_deformed_surface(self, source_surface, new_surface, coefs):
		"""Use cairo.Matrix to apply a transformation to `source_surface` using
		the coefficients in `coefs` and return a new surface with the result."""
		p_xx, p_yx, p_xy, p_yy, p_x0, p_y0 = coefs
		cairo_context = cairo.Context(new_surface)

		# m = cairo.Matrix(xx=1.0, yx=0.0, xy=0.0, yy=1.0, x0=0.0, y0=0.0)
		m = cairo.Matrix(xx=p_xx, yx=p_yx, xy=p_xy, yy=p_yy, x0=p_x0, y0=p_y0)
		try:
			cairo_context.transform(m)
		except:
			self.show_error(_("Error: invalid values"))
			return source_surface
		cairo_context.set_source_surface(source_surface, 0, 0)
		cairo_context.paint()
		return new_surface

	############################################################################

	def _update_expansion_rgba(self, event_btn=1):
		"""When the canvas grows, the color of the new pixels is parametrable"""
		color_type = self.get_option_value('crop-expand')
		self._force_expansion_rgba(color_type, event_btn)

	def _force_expansion_rgba(self, color_type, event_btn=1):
		if color_type == 'initial':
			exp_rgba = self.get_image().get_initial_rgba()
		elif color_type == 'secondary' and event_btn == 1:
			exp_rgba = self.window.options_manager.get_right_color()
		elif color_type == 'secondary' and event_btn == 3:
			exp_rgba = self.window.options_manager.get_left_color()
		else: # color_type == 'alpha':
			exp_rgba = Gdk.RGBA(red=1.0, green=1.0, blue=1.0, alpha=0.0)
		self._expansion_rgba = exp_rgba

	############################################################################
################################################################################

