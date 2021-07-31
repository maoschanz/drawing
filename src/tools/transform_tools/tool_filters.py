# tool_filters.py
#
# Copyright 2018-2021 Romain F. T.
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
from gi.repository import Gdk, GdkPixbuf, Gio
from .abstract_transform_tool import AbstractCanvasTool
from .filter_blur import FilterBlur
from .filter_colors import FilterColors
from .filter_contrast import FilterContrast
from .filter_emboss import FilterEmboss
from .filter_saturation import FilterSaturation
from .filter_transparency import FilterTransparency
from .filter_veil import FilterVeil
from .optionsbar_filters import OptionsBarFilters
from .utilities_blur import utilities_blur_surface, BlurType, BlurDirection

class ToolFilters(AbstractCanvasTool):
	__gtype_name__ = 'ToolFilters'

	def __init__(self, window):
		super().__init__('filters', _("Filters"), 'tool-filters-symbolic', window)
		self.cursor_name = 'pointer'

		self.add_tool_action_enum('filters_type', 'saturation')
		self.type_label = _("Change saturation")
		self._active_filter = 'saturation'

		# Options specific to filters, but which are here for no good reason
		self.add_tool_action_enum('filters_blur_dir', 'none')
		self.blur_algo = BlurType.INVALID

		# Initialisation of the filters
		self._all_filters = {
			'blur': FilterBlur('blur', self),
			'colors': FilterColors('colors', self),
			'contrast': FilterContrast('contrast', self),
			'emboss': FilterEmboss('emboss', self),
			'saturation': FilterSaturation('saturation', self),
			'transparency': FilterTransparency('transparency', self),
			'veil': FilterVeil('veil', self),
		}

	def try_build_pane(self):
		self.pane_id = 'filters'
		self.window.options_manager.try_add_bottom_pane(self.pane_id, self)

	def build_bottom_pane(self):
		self.bar = OptionsBarFilters(self.window, self)
		self.bar.menu_btn.connect('notify::active', self._set_active_type)
		self.bar.menu_btn.connect('notify::active', self._set_blur_direction)
		return self.bar

	def get_max_filter_width(self):
		width = 0
		for f in self._all_filters.values():
			width = max(f.get_preferred_minimum_width(), width)
		return width

	def set_filters_compact(self, is_compact):
		for f_id, f in self._all_filters.items():
			f.set_filter_compact(f_id == self._active_filter, is_compact)

	def get_options_label(self):
		return _("Active filter")

	def get_edition_status(self):
		tip_label = _("Click on the image to preview the selected filter")
		return self.type_label + ' - ' + tip_label

	############################################################################

	def _set_blur_direction(self, *args):
		self._all_filters['blur'].set_attributes_values()

	def _set_active_type(self, *args):
		state_as_string = self.get_option_value('filters_type')

		self.blur_algo = BlurType.INVALID
		if state_as_string == 'blur_fast':
			self.blur_algo = BlurType.CAIRO_REPAINTS
			self.type_label =  _("Fast blur")
			self._active_filter = 'blur'
		elif state_as_string == 'blur_slow':
			self.blur_algo = BlurType.PX_BOX
			self.type_label = _("Slow blur")
			self._active_filter = 'blur'
		elif state_as_string == 'tiles':
			self.blur_algo = BlurType.TILES
			self.type_label = _("Pixelization")
			self._active_filter = 'blur'

		elif state_as_string == 'saturation':
			self.type_label = _("Change saturation")
			self._active_filter = 'saturation'
		elif state_as_string == 'veil':
			self.type_label = _("Veil")
			self._active_filter = 'veil'

		elif state_as_string == 'contrast':
			self.type_label = _("Increase contrast")
			self._active_filter = 'contrast'
		# TODO changer la luminosity tant qu'à faire
		elif state_as_string == 'emboss':
			# Context: a filter. See "image embossing" on wikipedia
			self.type_label = _("Emboss")
			self._active_filter = 'emboss'

		elif state_as_string == 'invert':
			self.type_label = _("Invert colors")
			self._active_filter = 'colors'

		elif state_as_string == 'transparency':
			self.type_label = _("Add transparency")
			self._active_filter = 'transparency'
		else:
			self.type_label = _("Select a filter…")
		self.bar.on_filter_changed()

	############################################################################

	def on_tool_selected(self, *args):
		super().on_tool_selected()
		self._set_active_type()
		self._set_blur_direction()
		self.bar.menu_btn.set_active(True)
		if self.blur_algo == BlurType.INVALID:
			self.on_filter_preview()
			# XXX great optimization but it displays shit

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
			'filter_id': self._active_filter
		}
		options = self._all_filters[self._active_filter].build_filter_op()
		return {**operation, **options}

	def do_tool_operation(self, operation):
		self.start_tool_operation(operation)
		if operation['is_selection']:
			source_pixbuf = self.get_selection_pixbuf()
		else:
			source_pixbuf = self.get_main_pixbuf()

		active_filter = self._all_filters[operation['filter_id']]
		active_filter.do_filter_operation(source_pixbuf, operation)

		self.common_end_operation(operation)

	############################################################################
################################################################################

