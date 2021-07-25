# optionsbar_filters.py
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

from gi.repository import Gtk
from .abstract_optionsbar import AbstractOptionsBar
from .utilities import utilities_add_unit_to_spinbtn

class OptionsBarFilters(AbstractOptionsBar):
	__gtype_name__ = 'OptionsBarFilters'

	def __init__(self, window, filters_tool):
		super().__init__()
		self.window = window
		self.filters_tool = filters_tool

		self._build_ui('transform/abstract-optionsbar-transform.ui')
		builder = self._hydrate_transform_tool('transform/optionsbar-filters.ui')

		self.menu_btn = builder.get_object('menu_btn')
		self._togglable_btn = self.menu_btn
		self.menu_btn.set_menu_model(self.filters_tool.get_options_model())
		self._menu_label = builder.get_object('menu_label')
		self._menu_icon = builder.get_object('menu_icon')

	def add_spinbtn(self, caption, adj_as_array, spin_chars, unit):
		widget_label = Gtk.Label(label=caption)
		widget_spinbtn = Gtk.SpinButton(tooltip_text=caption)
		adj = Gtk.Adjustment()
		# it's [value, lower, upper, step_increment, page_increment, page_size]
		adj.configure(*adj_as_array)
		widget_spinbtn.set_adjustment(adj)
		utilities_add_unit_to_spinbtn(widget_spinbtn, spin_chars, unit)

		self.centered_box.add(widget_label)
		self.centered_box.add(widget_spinbtn)
		return widget_label, widget_spinbtn

	############################################################################

	def init_adaptability(self):
		super().init_adaptability()
		self._menu_icon.set_visible(False)
		widgets_size = self.filters_tool.get_max_filter_width()
		temp_limit_size = self.menu_btn.get_preferred_width()[0] + \
		                  50 + widgets_size + \
		                  self.cancel_btn.get_preferred_width()[0] + \
		                  self.help_btn.get_preferred_width()[0] + \
		                  self.apply_btn.get_preferred_width()[0]
		self._set_limit_size(temp_limit_size)

	def on_filter_changed(self):
		self.set_compact(self._is_narrow)
		self.window.set_picture_title()
		# self.menu_label.set_label(self.filters_tool.type_label) # XXX width???

	def set_compact(self, state):
		super().set_compact(state)
		self._menu_label.set_visible(not state)
		self._menu_icon.set_visible(state)
		self.filters_tool.set_filters_compact(state)

	############################################################################
################################################################################

