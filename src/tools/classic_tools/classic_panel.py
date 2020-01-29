# classic_panel.py
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
from .bottombar import DrawingAdaptativeBottomBar
from .color_popover import DrawingColorPopover
from .utilities import utilities_add_unit_to_spinbtn

################################################################################

class ClassicToolPanel(DrawingAdaptativeBottomBar):
	__gtype_name__ = 'ClassicToolPanel'

	def __init__(self, window):
		super().__init__()
		self.window = window
		builder = self.build_ui('ui/classic-panel.ui')

		self.color_box = builder.get_object('color_box')
		self.color_menu_btn_r = builder.get_object('color_menu_btn_r')
		self.color_menu_btn_l = builder.get_object('color_menu_btn_l')
		self._build_color_buttons(builder)

		self.options_btn = builder.get_object('options_btn')
		self.options_label = builder.get_object('options_label')
		self.options_long_box = builder.get_object('options_long_box')
		self.options_short_box = builder.get_object('options_short_box')

		self.thickness_scalebtn = builder.get_object('thickness_scalebtn')
		self.thickness_spinbtn = builder.get_object('thickness_spinbtn')
		self.thickness_spinbtn.set_value(self.window._settings.get_int('last-size'))
		utilities_add_unit_to_spinbtn(self.thickness_spinbtn, 3, 'px') # XXX works but is ugly

		self.minimap_btn = builder.get_object('minimap_btn')
		self.minimap_label = builder.get_object('minimap_label')
		self.minimap_arrow = builder.get_object('minimap_arrow')

	def update_for_new_tool(self, tool):
		self.color_box.set_sensitive(tool.use_color)
		self.thickness_scalebtn.set_sensitive(tool.use_size)
		self.thickness_spinbtn.set_sensitive(tool.use_size)

	def get_minimap_btn(self):
		return self.minimap_btn

	def set_minimap_label(self, label):
		self.minimap_label.set_label(label)

	def toggle_options_menu(self):
		self.options_btn.set_active(not self.options_btn.get_active())

	def hide_options_menu(self):
		self.options_btn.set_active(False)
		self._color_r.update_mode()
		self._color_l.update_mode()

	def build_options_menu(self, widget, model, label):
		if widget is not None:
			self.options_btn.set_popover(widget)
		elif model is not None:
			self.options_btn.set_menu_model(model)
		else:
			self.options_btn.set_popover(None)
		self.options_label.set_label(label)

	def init_adaptability(self):
		super().init_adaptability()
		temp_limit_size = self.color_box.get_preferred_width()[0] + \
		          self.thickness_spinbtn.get_preferred_width()[0] + \
		           self.options_long_box.get_preferred_width()[0] + \
		                self.minimap_btn.get_preferred_width()[0]
		self.set_limit_size(temp_limit_size)

	def set_compact(self, state):
		super().set_compact(state)
		self.options_long_box.set_visible(not state)
		self.options_short_box.set_visible(state)
		self.thickness_scalebtn.set_visible(state)
		self.thickness_spinbtn.set_visible(not state)
		self.minimap_arrow.set_visible(not state)

	############################################################################
	# Colors ###################################################################

	def middle_click_action(self):
		left_color = self._color_l.color_widget.get_rgba()
		self._color_l.color_widget.set_rgba(self._color_r.color_widget.get_rgba())
		self._color_r.color_widget.set_rgba(left_color)

	def set_operator(self, op_as_string):
		if op_as_string == 'difference':
			self._operator_enum = cairo.Operator.DIFFERENCE
			self._operator_label = _("Difference")
		elif op_as_string == 'source':
			self._operator_enum = cairo.Operator.SOURCE
			self._operator_label = _("Source color")
		elif op_as_string == 'clear':
			self._operator_enum = cairo.Operator.CLEAR
			self._operator_label = _("Erase")
		elif op_as_string == 'dest_in':
			self._operator_enum = cairo.Operator.DEST_IN
			self._operator_label = _("Blur")
		else:
			self._operator_enum = cairo.Operator.OVER
			self._operator_label = _("Classic")

	def _build_color_buttons(self, builder):
		"""Initialize the 2 color buttons and popovers with the 2 previously
		memorized RGBA values."""
		right_rgba = self.window._settings.get_strv('last-right-rgba')
		left_rgba = self.window._settings.get_strv('last-left-rgba')
		self._color_r = DrawingColorPopover(self.color_menu_btn_r, \
		      builder.get_object('r_btn_image'), right_rgba, False, self.window)
		self._color_l = DrawingColorPopover(self.color_menu_btn_l, \
		        builder.get_object('l_btn_image'), left_rgba, True, self.window)

	def set_palette_setting(self, show_editor):
		self._color_r.editor_setting_changed(show_editor)
		self._color_l.editor_setting_changed(show_editor)

	############################################################################
################################################################################

