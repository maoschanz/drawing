# options_manager.py
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

from gi.repository import GLib, Gio

class DrOptionsManager():
	__gtype_name__ = 'DrOptionsManager'
	# XXX this class should raise/catch more exceptions

	_tools_gsettings = Gio.Settings.new('com.github.maoschanz.drawing.tools-options')

	def __init__(self, window):
		self.window = window
		self._bottom_panes_dict = {}
		self._active_pane_id = None
		self._boolean_actions_from_gsetting = {}
		self._string_actions_from_gsetting = {}

	def _action_exists(self, name):
		return self.window.lookup_action(name) is not None

	############################################################################
	# Gio.Action for tool options ##############################################

	def add_option_boolean(self, name, default):
		if self._action_exists(name):
			return
		self.window.add_action_boolean(name, default, self._boolean_callback)

	def add_option_enum(self, name, default):
		if self._action_exists(name):
			return
		self.window.add_action_enum(name, default, self._enum_callback)

	def add_option_from_bool_key(self, action_name, key_name):
		default_value = self._tools_gsettings.get_boolean(key_name)
		self.add_option_boolean(action_name, default_value)
		self._boolean_actions_from_gsetting[action_name] = key_name
		return default_value

	def add_option_from_enum_key(self, action_name, key_name):
		default_value = self._tools_gsettings.get_string(key_name)
		self.add_option_enum(action_name, default_value)
		self._string_actions_from_gsetting[action_name] = key_name
		return default_value

	def get_value(self, name):
		if not self._action_exists(name):
			return
		action = self.window.lookup_action(name)
		if action.get_state_type().dup_string() == 's':
			return action.get_state().get_string()
		else:
			return action.get_state()

	def _boolean_callback(self, *args):
		"""This callback is simple but can't handle both menu-items and check/
		toggle-buttons. It is only good for menu-items and model-buttons."""
		new_value = args[1].get_boolean()

		args[0].set_state(GLib.Variant.new_boolean(new_value))
		self.window.set_picture_title()
		self.get_active_pane().hide_options_menu()

	def _enum_callback(self, *args):
		"""This callback is simple but can't handle both menu-items and
		radio-buttons. It is only good for menu-items and model-buttons."""
		new_value = args[1].get_string()

		# No need to change the state if it's already as the user want.
		# Cases "m1 m1" or "b1 b1" or "b1 m1" or "m1 b1"
		if new_value == args[0].get_state().get_string():
			return

		# Actually change the state to the new value.
		args[0].set_state(GLib.Variant.new_string(new_value))
		self.window.set_picture_title()
		self.get_active_pane().hide_options_menu()

	############################################################################

	def persist_tools_options(self, *args):
		"""Called before closing to persist the current values of a few options
		into gsettings (dconf or key-value file)."""

		# Panel-wide classic tools options (they are not Gio actions!)
		self._tools_gsettings.set_int('last-size', self.get_tool_width())
		self._persist_color(self.get_left_color(), 'last-left-rgba')
		self._persist_color(self.get_right_color(), 'last-right-rgba')

		# Tool-wide boolean actions
		for action_name in self._boolean_actions_from_gsetting:
			key_name = self._boolean_actions_from_gsetting[action_name]
			self._persist_boolean(action_name, key_name)

		# Tool-wide "enum" actions
		for action_name in self._string_actions_from_gsetting:
			key_name = self._string_actions_from_gsetting[action_name]
			self._persist_string(action_name, key_name)

	def _persist_string(self, action_name, key_name):
		action_value = self.get_value(action_name)
		self._tools_gsettings.set_string(key_name, action_value)

	def _persist_boolean(self, action_name, key_name):
		action_value = self.get_value(action_name)
		self._tools_gsettings.set_boolean(key_name, action_value)

	def _persist_color(self, rgba, key_name):
		rgba = [str(rgba.red), str(rgba.green), str(rgba.blue), str(rgba.alpha)]
		self._tools_gsettings.set_strv(key_name, rgba)

	############################################################################
	# Bottom panes management ##################################################

	def try_add_bottom_pane(self, pane_id, calling_tool):
		if pane_id not in self._bottom_panes_dict:
			new_pane = calling_tool.build_bottom_pane()
			if new_pane is None:
				return
			self._bottom_panes_dict[pane_id] = new_pane
			self.window.bottom_panes_box.add(new_pane.action_bar)

	def try_enable_pane(self, pane_id):
		if pane_id == self._active_pane_id:
			return
		elif pane_id not in self._bottom_panes_dict:
			# Shouldn't happen anyway
			return
		else:
			self._active_pane_id = pane_id
			self._show_active_pane()
			self.update_minimap_position()

	def _show_active_pane(self):
		for each_id in self._bottom_panes_dict:
			is_active = each_id == self._active_pane_id
			self._bottom_panes_dict[each_id].action_bar.set_visible(is_active)

	def get_active_pane(self):
		if self._active_pane_id is None:
			return None # XXX encore des exceptions manuelles...
			# return self._bottom_panes_dict['classic']
		return self._bottom_panes_dict[self._active_pane_id]

	def update_pane(self, tool):
		self._bottom_panes_dict[tool.pane_id].update_for_new_tool(tool)

	############################################################################

	def init_adaptability(self):
		for pane_id in self._bottom_panes_dict:
			self._bottom_panes_dict[pane_id].init_adaptability()
		self._show_active_pane()

	def adapt_to_window_size(self, available_width):
		self.get_active_pane().adapt_to_window_size(available_width)
		# Because the animation to show a bottom pane takes some time, it's
		# possible to change tool "too fast" (ctrl+b really quickly) and end up
		# in a situation where no pane is visible.
		# There is no easy fix for this as far as i know.
		# The following instruction "fixes" the problem just enough so users,
		# if they encounter it, will believe they dreamt the issue.
		self.get_active_pane().action_bar.set_visible(True)

	############################################################################

	def toggle_menu(self):
		self.get_active_pane().toggle_options_menu()

	def set_minimap_label(self, label):
		for pane_id in self._bottom_panes_dict:
			self._bottom_panes_dict[pane_id].set_minimap_label(label)

	def update_minimap_position(self):
		"""Move the minimap popover to the currently active optionsbar."""
		btn = self.get_active_pane().get_minimap_btn()
		if btn is not None:
			self.window.minimap.set_relative_to(btn)
		else:
			self.window.minimap.set_relative_to(self.window.bottom_panes_box)

	############################################################################
	# Methods specific to the optionsbar for classic tools #####################

	def get_classic_tools_pane(self): # XXX hardcoded
		return self._bottom_panes_dict['classic']

	def left_color_btn(self):
		return self.get_classic_tools_pane()._color_l

	def right_color_btn(self):
		return self.get_classic_tools_pane()._color_r

	def set_palette_setting(self, show_editor):
		self.get_classic_tools_pane().set_palette_setting(show_editor)

	def get_tool_width(self):
		return int(self.get_classic_tools_pane().thickness_spinbtn.get_value())

	def update_tool_width(self, delta):
		width = self.get_tool_width() + delta
		self.get_classic_tools_pane().thickness_spinbtn.set_value(width)

	def set_right_color(self, color):
		return self.right_color_btn().color_widget.set_rgba(color)

	def set_left_color(self, color):
		return self.left_color_btn().color_widget.set_rgba(color)

	def get_right_color(self):
		return self.right_color_btn().color_widget.get_rgba()

	def get_left_color(self):
		return self.left_color_btn().color_widget.get_rgba()

	def get_operator(self):
		# XXX répugnant, on duplique la donnée dans les 2 popovers, puis on
		# hardcode qu'on prendra la donnée uniquement dans celui de droite, et
		# tout ça sans respecter l'encapsulation
		enum = self.get_classic_tools_pane()._color_r._operator_enum
		label = self.get_classic_tools_pane()._color_r._operator_label
		return enum, label

	############################################################################
################################################################################

