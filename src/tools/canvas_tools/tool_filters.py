# tool_filters.py
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

import cairo
from gi.repository import Gdk, GdkPixbuf
from .abstract_canvas_tool import AbstractCanvasTool
from .optionsbar_filters import OptionsBarFilters
from .utilities_blur import utilities_blur_surface, BlurType, BlurDirection

class ToolFilters(AbstractCanvasTool):
	__gtype_name__ = 'ToolFilters'

	def __init__(self, window):
		super().__init__('filters', _("Filters"), 'tool-filters-symbolic', window)
		self.cursor_name = 'pointer'
		self.add_tool_action_simple('filters_preview', self.on_filter_preview)
		self.add_tool_action_enum('filters_type', 'saturation')
		self.add_tool_action_enum('filters_blur_dir', 'none')
		self.blur_direction = BlurDirection.BOTH
		self._reset_type_values()

	def try_build_pane(self):
		self.pane_id = 'filters'
		self.window.options_manager.try_add_bottom_pane(self.pane_id, self)

	def build_bottom_pane(self):
		self.bar = OptionsBarFilters(self.window, self)
		self.bar.menu_btn.connect('notify::active', self._set_active_type)
		self.bar.menu_btn.connect('notify::active', self._set_blur_direction)
		return self.bar

	def get_edition_status(self):
		tip_label = _("Click on the image to preview the selected filter")
		return self.type_label + ' - ' + tip_label

	############################################################################

	def _reset_type_values(self):
		self.blur_algo = BlurType.INVALID
		self.saturate = False
		self.pixelate = False
		self.invert = False
		self.transparency = False

	def _set_blur_direction(self, *args):
		state_as_string = self.get_option_value('filters_blur_dir')
		if state_as_string == 'none':
			self.blur_direction = BlurDirection.BOTH
		elif state_as_string == 'horizontal':
			self.blur_direction = BlurDirection.HORIZONTAL
		elif state_as_string == 'vertical':
			self.blur_direction = BlurDirection.VERTICAL

	def _set_active_type(self, *args):
		state_as_string = self.get_option_value('filters_type')
		self._reset_type_values()
		if state_as_string == 'blur_fast':
			self.blur_algo = BlurType.CAIRO_REPAINTS
			self.type_label =  _("Fast blur")
		elif state_as_string == 'blur_slow':
			self.blur_algo = BlurType.PX_BOX
			self.type_label = _("Slow blur")
		elif state_as_string == 'tiles':
			self.blur_algo = BlurType.TILES
			self.type_label = _("Pixelisation")
		elif state_as_string == 'saturation':
			self.saturate = True
			self.type_label = _("Change saturation")
		elif state_as_string == 'veil':
			self.pixelate = True
			self.type_label = _("Veil")
		elif state_as_string == 'invert':
			self.invert = True
			self.type_label = _("Invert colors")
		elif state_as_string == 'transparency':
			self.transparency = True
			self.type_label = _("Add transparency")
		else:
			self.type_label = _("Select a filter…")
		self.bar.on_filter_changed()

	def _get_saturation(self, *args):
		return self.bar.sat_btn.get_value()/100

	def _get_transparency(self, *args):
		return self.bar.tspc_btn.get_value()/100

	def _get_blur_radius(self, *args):
		return self.bar.blur_btn.get_value_as_int()

	############################################################################

	def on_tool_selected(self, *args):
		super().on_tool_selected()
		self._set_active_type()
		self._set_blur_direction()
		self.bar.menu_btn.set_active(True)
		if self.blur_algo == BlurType.INVALID:
			self.on_filter_preview()

	def on_press_on_area(self, event, surface, event_x, event_y):
		self.on_filter_preview()

	def on_filter_preview(self, *args):
		self._set_active_type()
		self._set_blur_direction()
		self.build_and_do_op()

	############################################################################

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'is_selection': self.apply_to_selection,
			'is_preview': True,
			'local_dx': 0,
			'local_dy': 0,
			'saturation': self._get_saturation(),
			'radius': self._get_blur_radius(),
			'pixelate': self.pixelate, # XXX ces 4 booléens dégueulasses au lieu
			'invert': self.invert, # de passer la valeur de l'action et de faire
			'saturate': self.saturate, # le switch/case côté do_tool_operation??
			'use_transparency': self.transparency,
			'transpercent': self._get_transparency(),
			'blur_algo': self.blur_algo,
			'blur_direction': self.blur_direction
		}
		return operation

	def op_invert_color(self, source_pixbuf):
		surface = Gdk.cairo_surface_create_from_pixbuf(source_pixbuf, 0, None)
		cairo_context = cairo.Context(surface)
		cairo_context.set_operator(cairo.Operator.DIFFERENCE)
		cairo_context.set_source_rgba(1.0, 1.0, 1.0, 1.0)
		cairo_context.paint()
		new_pixbuf = Gdk.pixbuf_get_from_surface(surface, 0, 0, \
		                              surface.get_width(), surface.get_height())
		self.get_image().set_temp_pixbuf(new_pixbuf)

	def op_transparency(self, source_pixbuf, percent):
		surface = Gdk.cairo_surface_create_from_pixbuf(source_pixbuf, 0, None)
		surface.set_device_scale(self.scale_factor(), self.scale_factor())
		width = source_pixbuf.get_width()
		height = source_pixbuf.get_height()
		new_surface = cairo.ImageSurface(cairo.Format.ARGB32, width, height)
		cairo_context = cairo.Context(new_surface)
		cairo_context.set_operator(cairo.Operator.SOURCE)
		cairo_context.set_source_surface(surface)
		cairo_context.paint_with_alpha(1.0 - percent)
		new_pixbuf = Gdk.pixbuf_get_from_surface(new_surface, 0, 0, \
		                      new_surface.get_width(), new_surface.get_height())
		self.get_image().set_temp_pixbuf(new_pixbuf)

	def op_blur(self, source_pixbuf, blur_algo, blur_direction, radius):
		surface = Gdk.cairo_surface_create_from_pixbuf(source_pixbuf, 0, None)
		surface.set_device_scale(self.scale_factor(), self.scale_factor())
		bs = utilities_blur_surface(surface, radius, blur_algo, blur_direction)
		bp = Gdk.pixbuf_get_from_surface(bs, 0, 0, bs.get_width(), bs.get_height())
		self.get_image().set_temp_pixbuf(bp)

	def do_tool_operation(self, operation):
		self.start_tool_operation(operation)
		if operation['is_selection']:
			source_pixbuf = self.get_selection_pixbuf()
		else:
			source_pixbuf = self.get_main_pixbuf()

		blur_algo = operation['blur_algo']
		if blur_algo != BlurType.INVALID:
			blur_radius = operation['radius']
			blur_direction = operation['blur_direction']
			self.op_blur(source_pixbuf, blur_algo, blur_direction, blur_radius)
		elif operation['use_transparency']:
			percent = operation['transpercent']
			self.op_transparency(source_pixbuf, percent)
		elif operation['invert']:
			self.op_invert_color(source_pixbuf)
		else:
			self.get_image().set_temp_pixbuf(source_pixbuf.copy())
			temp = self.get_image().temp_pixbuf
			if operation['saturate']:
				source_pixbuf.saturate_and_pixelate(temp, operation['saturation'], False)
			elif operation['pixelate']:
				source_pixbuf.saturate_and_pixelate(temp, 1, operation['pixelate'])

		self.common_end_operation(operation)

	############################################################################
################################################################################

