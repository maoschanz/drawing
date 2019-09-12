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

from gi.repository import Gtk, Gdk, GdkPixbuf
import cairo

from .utilities import utilities_fast_blur

from .abstract_canvas_tool import AbstractCanvasTool
from .bottombar import DrawingAdaptativeBottomBar

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

	def on_press_on_area(self, area, event, surface, event_x, event_y):
		self.on_filter_preview()

	def on_filter_preview(self, *args):
		self.set_active_type()
		self.update_temp_pixbuf()

	def get_saturation(self, *args):
		return self.bar.sat_btn.get_value()/100

	def get_blur_radius(self, *args):
		return int( self.bar.blur_btn.get_value() )

	def on_tool_selected(self, *args):
		super().on_tool_selected()
		self.set_active_type()
		self.bar.menu_btn.set_active(True)

	def get_edition_status(self):
		return self.label + ' - ' + self.type_label

	def reset_type_values(self):
		self.blur_algo = 10
		self.saturate = False
		self.pixelate = False
		self.invert = False

	def set_active_type(self, *args):
		state_as_string = self.get_option_value('filters_type')
		self.reset_type_values()
		if state_as_string == 'blur':
			self.blur_algo = 0
			self.type_label =  _("Blur")
		elif state_as_string == 'h_blur':
			self.blur_algo = 1
			self.type_label = _("Horizontal blur")
		elif state_as_string == 'v_blur':
			self.blur_algo = 2
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
		else:
			self.type_label = _("Select a filter…")
		self.bar.on_filter_changed()

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'is_selection': self.apply_to_selection,
			'is_preview': True,
			'saturation': self.get_saturation(),
			'radius': self.get_blur_radius(),
			'pixelate': self.pixelate,
			'invert': self.invert,
			'saturate': self.saturate,
			'blur_algo': self.blur_algo
		}
		return operation

	def do_tool_operation(self, operation):
		if operation['tool_id'] != self.id:
			return
		self.restore_pixbuf()
		if operation['is_selection']:
			source_pixbuf = self.get_selection_pixbuf()
		else:
			source_pixbuf = self.get_main_pixbuf()

		blur_algo = operation['blur_algo']
		if blur_algo != 10:
			blur_radius = operation['radius']
			surface = Gdk.cairo_surface_create_from_pixbuf(source_pixbuf, 0, None)
			blurred_surface = utilities_fast_blur(surface, blur_radius, 1, blur_algo)
			blurred_pixbuf = Gdk.pixbuf_get_from_surface(blurred_surface, 0, 0, \
			          blurred_surface.get_width(), blurred_surface.get_height())
			self.get_image().set_temp_pixbuf(blurred_pixbuf)
		elif operation['invert']:
			surface = Gdk.cairo_surface_create_from_pixbuf(source_pixbuf, 0, None)
			cairo_context = cairo.Context(surface)
			cairo_context.set_operator(cairo.Operator.DIFFERENCE)
			cairo_context.set_source_rgba(1.0, 1.0, 1.0, 1.0)
			cairo_context.paint()
			new_pixbuf = Gdk.pixbuf_get_from_surface(surface, 0, 0, \
			                          surface.get_width(), surface.get_height())
			self.get_image().set_temp_pixbuf(new_pixbuf)
		else:
			self.get_image().set_temp_pixbuf(source_pixbuf.copy())
			temp = self.get_image().get_temp_pixbuf()
			# source_pixbuf.saturate_and_pixelate(temp, operation['saturation'], operation['pixelate'])
			if operation['saturate']:
				source_pixbuf.saturate_and_pixelate(temp, operation['saturation'], False)
			elif operation['pixelate']:
				source_pixbuf.saturate_and_pixelate(temp, 1, operation['pixelate'])

		self.common_end_operation(operation['is_preview'], operation['is_selection'])

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
		self.blur_label = builder.get_object('blur_label')
		self.blur_btn = builder.get_object('blur_btn')
		self.preview_btn_narrow = builder.get_object('preview_btn_narrow')
		self.preview_btn_long = builder.get_object('preview_btn_long')

	def toggle_options_menu(self):
		self.menu_btn.set_active(not self.menu_btn.get_active())

	def init_adaptability(self):
		super().init_adaptability()
		self.menu_icon.set_visible(False)
		widgets_size = max( self.sat_label.get_preferred_width()[0] + \
		                    self.sat_btn.get_preferred_width()[0], \
		                    self.blur_label.get_preferred_width()[0] + \
		                    self.blur_btn.get_preferred_width()[0])
		temp_limit_size = self.menu_btn.get_preferred_width()[0] + 50 + \
		             widgets_size + self.cancel_btn.get_preferred_width()[0] + \
		                                 self.apply_btn.get_preferred_width()[0]
		self.set_limit_size(temp_limit_size)

	def on_filter_changed(self):
		self.set_compact(self.is_narrow)
		self.window.set_picture_title()

	def set_compact(self, state):
		super().set_compact(state)
		self.menu_label.set_visible(not state)
		self.menu_icon.set_visible(state)
		self.preview_btn_narrow.set_visible(state)
		self.preview_btn_long.set_visible(not state)

		blurring = (self.filters_tool.blur_algo != 10)
		self.sat_label.set_visible(self.filters_tool.saturate and not state)
		self.sat_btn.set_visible(self.filters_tool.saturate)
		self.blur_label.set_visible(blurring and not state)
		self.blur_btn.set_visible(blurring)

	############################################################################
################################################################################

