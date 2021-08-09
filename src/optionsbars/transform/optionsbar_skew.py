# optionsbar_skew.py
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

class OptionsBarSkew(AbstractOptionsBar):
	__gtype_name__ = 'OptionsBarSkew'

	def __init__(self):
		super().__init__()

		self._build_ui('transform/abstract-optionsbar-transform.ui')
		builder = self._hydrate_transform_tool('transform/optionsbar-skew.ui')

		self.xy_label = builder.get_object('xy_label')
		self.yx_label = builder.get_object('yx_label')
		self.separator = builder.get_object('separator')

		self.yx_spinbtn = builder.get_object('yx_spinbtn')
		self.xy_spinbtn = builder.get_object('xy_spinbtn')
		utilities_add_unit_to_spinbtn(self.yx_spinbtn, 3, '%')
		utilities_add_unit_to_spinbtn(self.xy_spinbtn, 3, '%')

	def init_adaptability(self):
		super().init_adaptability()
		temp_limit_size = self.centered_box.get_preferred_width()[0] + \
		                    self.cancel_btn.get_preferred_width()[0] + \
		                      self.help_btn.get_preferred_width()[0] + \
		                     self.apply_btn.get_preferred_width()[0]
		self._set_limit_size(temp_limit_size)

	def update_for_new_tool(self, tool):
		self.set_compact(self._is_narrow)

	def set_compact(self, state):
		super().set_compact(state)
		if state:
			self.centered_box.set_orientation(Gtk.Orientation.VERTICAL)
		else:
			self.centered_box.set_orientation(Gtk.Orientation.HORIZONTAL)
		self.xy_label.set_visible(not state)
		self.yx_label.set_visible(not state)
		self.separator.set_visible(not state)

	############################################################################
################################################################################

