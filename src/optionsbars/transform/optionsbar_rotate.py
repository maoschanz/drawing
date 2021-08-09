# optionsbar_rotate.py
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

class OptionsBarRotate(AbstractOptionsBar):
	__gtype_name__ = 'OptionsBarRotate'

	def __init__(self, rotate_tool):
		super().__init__()
		# knowing the tool is needed because the pane doesn't compact the same
		# way if it's applied to the selection
		self.rotate_tool = rotate_tool

		self._build_ui('transform/abstract-optionsbar-transform.ui')
		builder = self._hydrate_transform_tool('transform/optionsbar-rotate.ui')

		self.angle_btn = builder.get_object('angle_btn')
		utilities_add_unit_to_spinbtn(self.angle_btn, 3, '°')

		self.angle_box = builder.get_object('angle_box')
		self.rotate_box = builder.get_object('rotate_box')
		self.flip_box = builder.get_object('flip_box')

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
		if self.rotate_tool.apply_to_selection:
			self.options_btn.set_visible(state)
			self.angle_box.set_visible(True)
			self.rotate_box.set_visible(not state)
			self.flip_box.set_visible(not state)
		else:
			self.options_btn.set_visible(False)
			self.angle_box.set_visible(False)
			self.rotate_box.set_visible(True)
			self.flip_box.set_visible(True)

	############################################################################
################################################################################

