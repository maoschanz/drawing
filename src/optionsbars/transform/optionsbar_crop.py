# optionsbar_crop.py
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

class OptionsBarCrop(AbstractOptionsBar):
	__gtype_name__ = 'OptionsBarCrop'

	def __init__(self):
		super().__init__()

		self._build_ui('transform/abstract-optionsbar-transform.ui')
		builder = self._hydrate_transform_tool('transform/optionsbar-crop.ui')

		self.height_btn = builder.get_object('height_btn')
		self.width_btn = builder.get_object('width_btn')
		utilities_add_unit_to_spinbtn(self.height_btn, 4, 'px')
		utilities_add_unit_to_spinbtn(self.width_btn, 4, 'px')
		# XXX top/bottom/left/right ?

		self.width_label = builder.get_object('width_label')
		self.height_label = builder.get_object('height_label')
		self.separator = builder.get_object('separator')

	def init_adaptability(self):
		super().init_adaptability()
		temp_limit_size = self.centered_box.get_preferred_width()[0] + \
		                    self.cancel_btn.get_preferred_width()[0] + \
		                   self.options_btn.get_preferred_width()[0] + \
		                      self.help_btn.get_preferred_width()[0] + \
		                     self.apply_btn.get_preferred_width()[0]
		self._set_limit_size(temp_limit_size)

	def set_compact(self, state):
		super().set_compact(state)
		if state:
			self.centered_box.set_orientation(Gtk.Orientation.VERTICAL)
		else:
			self.centered_box.set_orientation(Gtk.Orientation.HORIZONTAL)
		self.width_label.set_visible(not state)
		self.height_label.set_visible(not state)
		self.separator.set_visible(not state)

		# if self.crop_tool.apply_to_selection:
		# 	self.???.set_visible(state)
		# else:
		# 	self.???.set_visible(state)

	############################################################################
################################################################################

