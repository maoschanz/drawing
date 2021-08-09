# optionsbar_classic.py
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
from .abstract_optionsbar import AbstractOptionsBar
from .optionsbar_color_popover import OptionsBarClassicColorPopover
from .utilities import utilities_add_unit_to_spinbtn

################################################################################

class OptionsBarClassic(AbstractOptionsBar):
	__gtype_name__ = 'OptionsBarClassic'

	def __init__(self, window):
		super().__init__()
		self.window = window
		builder = self._build_ui('classic/optionsbar-classic.ui')

		self.color_box = builder.get_object('color_box')
		self.color_menu_btn_r = builder.get_object('color_menu_btn_r')
		self.color_menu_btn_l = builder.get_object('color_menu_btn_l')
		self._build_color_buttons(builder)

		window.add_action_enum('cairo_operator', 'over', self._cairo_op_changed)
		window.add_action_enum('cairo_op_mirror', 'over', self._cairop_mirror)
		self._cairo_operator_lock = False

		self.options_label = builder.get_object('options_label')
		self.options_long_box = builder.get_object('options_long_box')
		self.options_short_box = builder.get_object('options_short_box')

		self.thickness_scalebtn = builder.get_object('thickness_scalebtn')
		self.thickness_spinbtn = builder.get_object('thickness_spinbtn')
		last_size = self._get_tool_options().get_int('last-size')
		self.thickness_spinbtn.set_value(last_size)
		utilities_add_unit_to_spinbtn(self.thickness_spinbtn, 3, 'px')

		self.minimap_btn = builder.get_object('minimap_btn')
		self.minimap_label = builder.get_object('minimap_label')
		self.minimap_arrow = builder.get_object('minimap_arrow')

	def _get_tool_options(self):
		return self.window.options_manager._tools_gsettings

	def update_for_new_tool(self, tool):
		self.color_box.set_sensitive(tool.use_color)
		if tool.use_operator:
			operator = self.window.options_manager.get_value('cairo_operator')
		else:
			operator = tool._fallback_operator
		self._color_r.set_operators_available(tool.use_operator, operator)
		self._color_l.set_operators_available(tool.use_operator, operator)
		self.thickness_scalebtn.set_sensitive(tool.use_size)
		self.thickness_spinbtn.set_sensitive(tool.use_size)

	def get_minimap_btn(self):
		return self.minimap_btn

	def set_minimap_label(self, label):
		self.minimap_label.set_label(label)

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
		                self.minimap_btn.get_preferred_width()[0] + 50
		# assuming 50px is enough to compensate the length of the label
		self._set_limit_size(temp_limit_size)

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

	def _build_color_buttons(self, builder):
		"""Initialize the 2 color-buttons and popovers with the 2 previously
		memorized RGBA values."""
		right_rgba = self._get_tool_options().get_strv('last-right-rgba')
		left_rgba = self._get_tool_options().get_strv('last-left-rgba')
		self._color_r = OptionsBarClassicColorPopover(self.color_menu_btn_r, \
		             builder.get_object('r_btn_image'), right_rgba, False, self)
		self._color_l = OptionsBarClassicColorPopover(self.color_menu_btn_l, \
		               builder.get_object('l_btn_image'), left_rgba, True, self)

	def set_palette_setting(self, show_editor):
		self._color_r.editor_setting_changed(show_editor)
		self._color_l.editor_setting_changed(show_editor)

	############################################################################
	# Cairo operators ("color application modes") ##############################

	def _cairo_op_changed(self, *args):
		"""This action can be used in menus. It's a custom callback because it
		has to set the lock required to be avoid infinite recursion caused by
		the synchronisation with `win.cairo_op_mirror`"""
		self.window.options_manager._enum_callback(*args)
		# XXX appels au callback PRIVÉ de l'options_manager

		mirrored_action = self.window.lookup_action('cairo_op_mirror')
		if args[1].get_string() == mirrored_action.get_state().get_string():
			return
		self._cairo_operator_lock = True
		self.window.options_manager._enum_callback(mirrored_action, args[1])
		self._cairo_operator_lock = False
		self._update_popovers(args[1].get_string())

	def _update_popovers(self, op_as_string):
		self._color_r.adapt_to_operator(op_as_string)
		self._color_l.adapt_to_operator(op_as_string)

	def _cairop_mirror(self, *args):
		"""This action should NEVER be added to any menu. It mirrors the action
		`win.cairo_operator`, which can be added to menus. This action is
		intended to be used by GtkRadioButtons, whose weird behaviors include
		sending a `change-state` signal when being unchecked, thus triggering
		this callback twice. So this synchronisation mechanism is needed, with
		an other "classic" action duplicating the data, and a lock."""
		if self._cairo_operator_lock:
			return
		if args[1].get_string() == args[0].get_state().get_string():
			return
		mirrored_action = self.window.lookup_action('cairo_operator')
		if args[1].get_string() == mirrored_action.get_state().get_string():
			return
		self.window.options_manager._enum_callback(*args)
		# XXX appels au callback PRIVÉ de l'options_manager
		self._cairo_operator_lock = True
		self.window.options_manager._enum_callback(mirrored_action, args[1])
		self._cairo_operator_lock = False
		self._update_popovers(args[1].get_string())

	############################################################################
################################################################################

