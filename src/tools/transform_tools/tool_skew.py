# tool_skew.py
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
from gi.repository import Gdk
from .abstract_transform_tool import AbstractCanvasTool
from .optionsbar_skew import OptionsBarSkew
from .utilities_overlay import utilities_show_handles_on_context
from .utilities_colors import utilities_gdk_rgba_to_normalized_array

class ToolSkew(AbstractCanvasTool):
	__gtype_name__ = 'ToolSkew'

	def __init__(self, window):
		# This is the name of the tool changing rectangles into parallelograms.
		# It's synonymous with tilt, slant, bend. If you need a reference to
		# translate it, this is named after MS Paint's "Stretch/Skew" dialog.
		super().__init__('skew', _("Skew"), 'tool-skew-symbolic', window)
		self._x = 0
		self._y = 0
		self.add_tool_action_simple('skew-exists', self.select_flowbox_child)
		self.add_tool_action_enum('crop-expand', 'initial')

	def try_build_pane(self):
		self.pane_id = 'skew'
		self.window.options_manager.try_add_bottom_pane(self.pane_id, self)

	def build_bottom_pane(self):
		bar = OptionsBarSkew()
		self.yx_spinbtn = bar.yx_spinbtn
		self.xy_spinbtn = bar.xy_spinbtn
		self.yx_spinbtn.connect('value-changed', self.on_coord_changed)
		self.xy_spinbtn.connect('value-changed', self.on_coord_changed)
		return bar

	def get_options_model(self):
		if self.apply_to_selection:
			return None
		else:
			return super().get_options_model()

	def get_options_label(self):
		if self.apply_to_selection:
			return super().get_options_label()
		else:
			return _("Skewing options")

	def get_editing_tips(self):
		label_direction = _("The directions of the deformation are hinted by the mouse pointer")

		label_modifiers = None
		if self.apply_to_selection:
			label_action = _("Skewing the selection")
			label_confirm = None
		else:
			label_action = _("Skewing the canvas")
			label_confirm = self.label + " - " + \
			                         _("Don't forget to confirm the operation!")
			if not self.get_image().get_mouse_is_pressed():
				label_modifiers = _("Press <Alt>, <Shift>, or both, to " + \
				                      "quickly change the 'expand with' option")

		full_list = [label_action, label_direction, label_confirm, label_modifiers]
		return list(filter(None, full_list))

	def on_tool_selected(self, *args):
		super().on_tool_selected()
		self.set_action_sensitivity('crop-expand', not self.apply_to_selection)
		self._reset_values()

	############################################################################

	def get_yx(self):
		return self.yx_spinbtn.get_value_as_int()

	def get_xy(self):
		return self.xy_spinbtn.get_value_as_int()

	def _set_cursor_name(self):
		if self._directions == '':
			self.cursor_name = 'not-allowed'
			return
		if self._directions == 'nw' or self._directions == 'se':
			self.cursor_name = 'nwse-resize'
		elif self._directions == 'ne' or self._directions == 'sw':
			self.cursor_name = 'nesw-resize'
		elif self._directions == 'n' or self._directions == 's':
			self.cursor_name = 'ew-resize'
		elif self._directions == 'e' or self._directions == 'w':
			self.cursor_name = 'ns-resize'

	def _get_width(self):
		if self.apply_to_selection:
			source_pixbuf = self.get_selection_pixbuf()
		else:
			source_pixbuf = self.get_main_pixbuf()
		return source_pixbuf.get_width()

	def _get_height(self):
		if self.apply_to_selection:
			source_pixbuf = self.get_selection_pixbuf()
		else:
			source_pixbuf = self.get_main_pixbuf()
		return source_pixbuf.get_height()

	def on_coord_changed(self, *args):
		self.build_and_do_op()

	def _reset_values(self, *args):
		self._update_expansion_rgba()
		self._yx = 0 # vertical deformation
		self._xy = 0 # horizontal deformation
		self.yx_spinbtn.set_value(0)
		self.xy_spinbtn.set_value(0)
		self.build_and_do_op()

	############################################################################

	def on_unclicked_motion_on_area(self, event, surface):
		self.set_directional_cursor(event.x, event.y)

	def on_press_on_area(self, event, surface, event_x, event_y):
		self.x_press = event_x
		self.y_press = event_y
		self._yx = self.get_yx() # vertical deformation
		self._xy = self.get_xy() # horizontal deformation
		# TODO répliquer ce que fait le scale avec son x2/y2 qui évite un effet
		# flamby dégueulasse lié aux arrondis ?
		self._update_expansion_rgba(event.button)

		self.update_modifier_state(event.state)
		if 'SHIFT' in self._modifier_keys and 'ALT' in self._modifier_keys:
			self._force_expansion_rgba('secondary', event.button)
		elif 'SHIFT' in self._modifier_keys:
			self._force_expansion_rgba('alpha')
		elif 'ALT' in self._modifier_keys:
			self._force_expansion_rgba('initial')

	def on_motion_on_area(self, event, surface, event_x, event_y, render=True):
		if self._directions == '' or not render:
			return

		delta_x = event_x - self.x_press
		delta_y = event_y - self.y_press

		yx = self._yx
		xy = self._xy
		if 'n' in self._directions:
			xy -= 100 * delta_x/self._get_width()
		if 's' in self._directions:
			xy += 100 * delta_x/self._get_width()
		if 'w' in self._directions:
			yx -= 100 * delta_y/self._get_height()
		if 'e' in self._directions:
			yx += 100 * delta_y/self._get_height()

		self.yx_spinbtn.set_value(yx)
		self.xy_spinbtn.set_value(xy)

	def on_release_on_area(self, event, surface, event_x, event_y):
		self.on_motion_on_area(event, surface, event_x, event_y)
		self.build_and_do_op() # technically already done

	############################################################################

	def on_draw_above(self, area, cairo_context):
		x1 = 0
		y1 = 0
		scaled_xy = abs(self.get_xy()) * (self._get_height() /  self._get_width())
		scaled_yx = abs(self.get_yx()) * (self._get_width() /  self._get_height())
		p_xy = (scaled_xy + 100) / 100
		p_yx = (scaled_yx + 100) / 100
		x2 = x1 + self._get_width() * p_xy
		y2 = y1 + self._get_height() * p_yx

		x1, x2, y1, y2 = self.get_image().get_corrected_coords(x1, x2, y1, y2, \
		                                         self.apply_to_selection, False)
		self._draw_temp_pixbuf(cairo_context, x1, y1)
		thickness = self.get_overlay_thickness()
		utilities_show_handles_on_context(cairo_context, x1, x2, y1, y2, thickness)

	############################################################################

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'is_selection': self.apply_to_selection,
			'is_preview': True,
			'local_dx': 0,
			'local_dy': 0,
			'yx': self.yx_spinbtn.get_value_as_int()/100,
			'xy': self.xy_spinbtn.get_value_as_int()/100,
			'rgba': self._expansion_rgba,
		}
		return operation

	def do_tool_operation(self, operation):
		self.start_tool_operation(operation)
		if operation['is_selection']:
			source_pixbuf = self.get_selection_pixbuf()
			prefill = False
		else:
			source_pixbuf = self.get_main_pixbuf()
			prefill = True
		source_surface = Gdk.cairo_surface_create_from_pixbuf(source_pixbuf, 0, None)
		source_surface.set_device_scale(self.scale_factor(), self.scale_factor())
		w0 = source_surface.get_width()
		h0 = source_surface.get_height()

		xy = operation['xy']
		x0 = 0.0
		if xy < 0:
			x0 = int(-1 * xy * h0)
		yx = operation['yx']
		y0 = 0.0
		if yx < 0:
			y0 = int(-1 * yx * w0)
		coefs = [1.0, yx, xy, 1.0, x0, y0]

		new_surface = self.get_deformed_surface(source_surface, coefs)
		if prefill:
			w = new_surface.get_width()
			h = new_surface.get_height()
			cairo_context = cairo.Context(new_surface)
			color_array = utilities_gdk_rgba_to_normalized_array(self._expansion_rgba)
			cairo_context.set_source_rgba(*color_array)

			# Doing only one path is possible but it's a mess: as a dumbass, i
			# prefer to draw 4 simple triangles
			if yx != 0:
				# Top triangle
				cairo_context.new_path()
				cairo_context.move_to(0, 0)
				if xy >= 0:
					if yx >= 0:
						x_new = 0
						y_new = 0
					else:
						cairo_context.line_to(w0, 0)
						x_new = 1.0 * 0 + xy * 0 + x0
						y_new = yx * 0 + 1.0 * 0 + y0
				else:
					if yx >= 0:
						x_new = 0
						y_new = 0
					else:
						cairo_context.line_to(w, 0)
						x_new = 1.0 * 0 + xy * 0 + x0
						y_new = yx * 0 + 1.0 * 0 + y0
				cairo_context.line_to(x_new, y_new)
				cairo_context.close_path()
				cairo_context.fill()

				# Bottom triangle
				cairo_context.new_path()
				cairo_context.close_path()
				cairo_context.fill()

			if xy != 0:
				# Right triangle
				cairo_context.new_path()
				cairo_context.close_path()
				cairo_context.fill()

				# Left triangle
				cairo_context.new_path()
				cairo_context.close_path()
				cairo_context.fill()

		new_pixbuf = Gdk.pixbuf_get_from_surface(new_surface, 0, 0, \
		                      new_surface.get_width(), new_surface.get_height())
		self.get_image().set_temp_pixbuf(new_pixbuf)
		self.common_end_operation(operation)

	############################################################################
################################################################################

