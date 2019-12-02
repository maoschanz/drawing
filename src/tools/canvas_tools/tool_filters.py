# tool_filters.py
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

import cairo
from gi.repository import Gtk, Gdk, GdkPixbuf

from .abstract_canvas_tool import AbstractCanvasTool
from .bottombar import DrawingAdaptativeBottomBar

from .utilities_tools import utilities_fast_blur
from .utilities_tools import BlurType
from .utilities import utilities_add_unit_to_spinbtn

class ToolFilters(AbstractCanvasTool):
	__gtype_name__ = 'ToolFilters'

	def __init__(self, window):
		super().__init__('filters', _("Filters"), 'tool-blur-symbolic', window)
		self.cursor_name = 'pointer'
		self.apply_to_selection = False
		self.add_tool_action_simple('filters_preview', self.on_filter_preview)
		self.add_tool_action_enum('filters_type', 'none')
		self.reset_type_values()

	def try_build_panel(self):
		self.panel_id = 'filters'
		self.window.options_manager.try_add_bottom_panel(self.panel_id, self)

	def build_bottom_panel(self):
		self.bar = FiltersToolPanel(self.window, self)
		self.bar.menu_btn.connect('notify::active', self.set_active_type)
		return self.bar

	def on_press_on_area(self, event, surface, event_x, event_y):
		self.on_filter_preview()

	def on_filter_preview(self, *args):
		self.set_active_type()
		self.build_and_do_op()

	def get_saturation(self, *args):
		return self.bar.sat_btn.get_value()/100

	def get_transparency(self, *args):
		return self.bar.tspc_btn.get_value()/100

	def get_blur_radius(self, *args):
		return int( self.bar.blur_btn.get_value() )

	def on_tool_selected(self, *args):
		super().on_tool_selected()
		self.set_active_type()
		self.bar.menu_btn.set_active(True)
		if self.blur_algo == BlurType.INVALID:
			self.on_filter_preview()

	def get_edition_status(self):
		tip_label = _("Click on the image to preview the selected filter")
		return self.type_label + ' - ' + tip_label

	def reset_type_values(self):
		self.blur_algo = BlurType.INVALID
		self.saturate = False
		self.pixelate = False
		self.invert = False
		self.transparency = False

	def set_active_type(self, *args):
		state_as_string = self.get_option_value('filters_type')
		self.reset_type_values()
		if state_as_string == 'blur':
			self.blur_algo = BlurType.AUTO # BlurType.PX_BOX
			self.type_label =  _("Blur")
		elif state_as_string == 'h_blur':
			self.blur_algo = BlurType.PX_HORIZONTAL
			self.type_label = _("Horizontal blur")
		elif state_as_string == 'v_blur':
			self.blur_algo = BlurType.PX_VERTICAL
			self.type_label = _("Vertical blur")
		elif state_as_string == 'saturation':
			self.saturate = True
			self.type_label = _("Saturation")
		elif state_as_string == 'pixels':
			self.pixelate = True
			self.type_label = _("Pixelisation")
		elif state_as_string == 'invert':
			self.invert = True
			self.type_label = _("Invert colors")
		elif state_as_string == 'transparency':
			self.transparency = True
			self.type_label = _("Transparency")
		else:
			self.type_label = _("Select a filter…")
		self.bar.on_filter_changed()

	############################################################################

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'is_selection': self.apply_to_selection,
			'is_preview': True,
			'local_dx': 0,
			'local_dy': 0,
			'saturation': self.get_saturation(),
			'radius': self.get_blur_radius(),
			'pixelate': self.pixelate,
			'invert': self.invert,
			'saturate': self.saturate,
			'use_transparency': self.transparency,
			'transpercent': self.get_transparency(),
			'blur_algo': self.blur_algo
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

	def op_blur(self, source_pixbuf, blur_algo, blur_radius):
		surface = Gdk.cairo_surface_create_from_pixbuf(source_pixbuf, 0, None)
		bs = utilities_fast_blur(surface, blur_radius, blur_algo)
		bp = Gdk.pixbuf_get_from_surface(bs, 0, 0, bs.get_width(), bs.get_height())
		self.get_image().set_temp_pixbuf(bp)

	def do_tool_operation(self, operation):
		if operation['tool_id'] != self.id:
			return
		self.restore_pixbuf()
		if operation['is_selection']:
			source_pixbuf = self.get_selection_pixbuf()
		else:
			source_pixbuf = self.get_main_pixbuf()

		blur_algo = operation['blur_algo']
		if blur_algo != BlurType.INVALID:
			blur_radius = operation['radius']
			self.op_blur(source_pixbuf, blur_algo, blur_radius)
		elif operation['use_transparency']:
			percent = operation['transpercent']
			self.op_transparency(source_pixbuf, percent)
		elif operation['invert']:
			self.op_invert_color(source_pixbuf)
		else:
			self.get_image().set_temp_pixbuf(source_pixbuf.copy())
			temp = self.get_image().get_temp_pixbuf()
			if operation['saturate']:
				source_pixbuf.saturate_and_pixelate(temp, operation['saturation'], False)
			elif operation['pixelate']:
				source_pixbuf.saturate_and_pixelate(temp, 1, operation['pixelate'])

		self.common_end_operation(operation)

	############################################################################
################################################################################

class FiltersToolPanel(DrawingAdaptativeBottomBar):
	__gtype_name__ = 'FiltersToolPanel'

	def __init__(self, window, filters_tool):
		super().__init__()
		self.window = window
		self.filters_tool = filters_tool
		builder = self.build_ui('tools/ui/tool_filters.ui')
		self.menu_btn = builder.get_object('menu_btn')
		self.menu_label = builder.get_object('menu_label')
		self.menu_icon = builder.get_object('menu_icon')

		self.sat_label = builder.get_object('sat_label')
		self.sat_btn = builder.get_object('sat_btn')
		utilities_add_unit_to_spinbtn(self.sat_btn, 3, '%')

		self.tspc_label = builder.get_object('tspc_label')
		self.tspc_btn = builder.get_object('tspc_btn')
		utilities_add_unit_to_spinbtn(self.tspc_btn, 3, '%')

		self.blur_label = builder.get_object('blur_label')
		self.blur_btn = builder.get_object('blur_btn')
		utilities_add_unit_to_spinbtn(self.blur_btn, 2, 'px')

	def toggle_options_menu(self):
		self.menu_btn.set_active(not self.menu_btn.get_active())

	def init_adaptability(self):
		super().init_adaptability()
		self.menu_icon.set_visible(False)
		widgets_size = max( self.sat_label.get_preferred_width()[0] + \
		                    self.sat_btn.get_preferred_width()[0], \
		                    self.tspc_label.get_preferred_width()[0] + \
		                    self.tspc_btn.get_preferred_width()[0], \
		                    self.blur_label.get_preferred_width()[0] + \
		                    self.blur_btn.get_preferred_width()[0])
		temp_limit_size = self.menu_btn.get_preferred_width()[0] + \
		                  50 + widgets_size + \
		                  self.cancel_btn.get_preferred_width()[0] + \
		                  self.apply_btn.get_preferred_width()[0]
		self.set_limit_size(temp_limit_size)

	def on_filter_changed(self):
		self.set_compact(self.is_narrow)
		self.window.set_picture_title()

	def set_compact(self, state):
		super().set_compact(state)
		self.menu_label.set_visible(not state)
		self.menu_icon.set_visible(state)

		blurring = (self.filters_tool.blur_algo != BlurType.INVALID)
		self.tspc_label.set_visible(self.filters_tool.transparency and not state)
		self.tspc_btn.set_visible(self.filters_tool.transparency)
		self.sat_label.set_visible(self.filters_tool.saturate and not state)
		self.sat_btn.set_visible(self.filters_tool.saturate)
		self.blur_label.set_visible(blurring and not state)
		self.blur_btn.set_visible(blurring)

	############################################################################
################################################################################

