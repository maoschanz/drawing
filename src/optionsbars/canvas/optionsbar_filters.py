# optionsbar_filters.py
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

from .abstract_optionsbar import AbstractOptionsBar
from .utilities_blur import BlurType
from .utilities import utilities_add_unit_to_spinbtn

class OptionsBarFilters(AbstractOptionsBar):
	__gtype_name__ = 'OptionsBarFilters'

	def __init__(self, window, filters_tool):
		super().__init__()
		self.window = window
		self.filters_tool = filters_tool
		builder = self.build_ui('optionsbars/canvas/optionsbar-filters.ui')
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

	############################################################################

	def toggle_options_menu(self):
		self.menu_btn.set_active(not self.menu_btn.get_active())

	def hide_options_menu(self):
		self.menu_btn.set_active(False)

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
		self.set_compact(self._is_narrow)
		self.window.set_picture_title()
		self.menu_label.set_label(self.filters_tool.type_label)

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

