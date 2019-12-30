# options_manager.py
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

from gi.repository import GLib

class DrawingOptionsManager():
	__gtype_name__ = 'DrawingOptionsManager'
	# TODO this class should raise/catch exceptions instead of trusting me

	def __init__(self, window):
		self.window = window
		self.cached_value1 = None
		self.cached_value2 = None
		self.bottom_panels_dict = {}
		self.active_panel = None

	############################################################################
	# Gio.Action for tool options ##############################################

	def add_tool_option_boolean(self, name, default):
		if self.window.lookup_action(name) is not None:
			return
		self.window.add_action_boolean(name, default, self.boolean_callback)

	def add_tool_option_enum(self, name, default):
		if self.window.lookup_action(name) is not None:
			return
		self.window.add_action_enum(name, default, self.enum_callback)

	def add_tool_option_enum_radio(self, name, default):
		if self.window.lookup_action(name) is not None:
			return
		self.window.add_action_enum(name, default, self.enum_callback_radio)

	def get_value(self, name):
		if self.window.lookup_action(name) is None:
			return
		action = self.window.lookup_action(name)
		if action.get_state_type().dup_string() is 's':
			return action.get_state().get_string()
		else:
			return action.get_state()

	def boolean_callback(self, *args):
		new_value = args[1].get_boolean()
		# current_value = args[0].get_state()
		args[0].set_state(GLib.Variant.new_boolean(new_value))
		self.window.set_picture_title()
		self.get_active_panel().hide_options_menu()

	def enum_callback(self, *args):
		"""This callback is simple but can't handle both menu-items and
		radio-buttons. It is only good for menu-items and model-buttons."""
		new_value = args[1].get_string()
		current_value = args[0].get_state().get_string()

		# No need to change the state if it's already as the user want.
		# Cases "m1 m1" or "b1 b1" or "b1 m1" or "m1 b1"
		if new_value == current_value:
			return

		# Actually change the state to the new value.
		args[0].set_state(GLib.Variant.new_string(new_value))
		self.window.set_picture_title()
		self.get_active_panel().hide_options_menu()

	############################################################################
	# Bottom panels management #################################################

	def try_add_bottom_panel(self, panel_id, calling_tool):
		if panel_id not in self.bottom_panels_dict:
			new_panel = calling_tool.build_bottom_panel()
			if new_panel is None:
				return
			self.bottom_panels_dict[panel_id] = new_panel
			self.window.bottom_panel_box.add(new_panel.action_bar)

	def try_enable_panel(self, panel_id):
		if panel_id == self.active_panel:
			return
		elif panel_id not in self.bottom_panels_dict:
			# Shouldn't happen anyway
			return
		else:
			self.active_panel = panel_id
			self.show_active_panel()
			self.update_minimap_position()

	def show_active_panel(self):
		for each_id in self.bottom_panels_dict:
			if each_id == self.active_panel:
				self.bottom_panels_dict[self.active_panel].action_bar.set_visible(True)
			else:
				self.bottom_panels_dict[each_id].action_bar.set_visible(False)

	def get_active_panel(self):
		if self.active_panel is None:
			return None # XXX encore des exceptions manuelles...
		return self.bottom_panels_dict[self.active_panel]

	def update_panel(self, tool):
		self.bottom_panels_dict[tool.panel_id].update_for_new_tool(tool)

	############################################################################

	def init_adaptability(self):
		for panel_id in self.bottom_panels_dict:
			self.bottom_panels_dict[panel_id].init_adaptability()
		self.show_active_panel()

	def adapt_to_window_size(self, available_width):
		self.get_active_panel().adapt_to_window_size(available_width)

	############################################################################

	def toggle_menu(self):
		self.get_active_panel().toggle_options_menu()

	def set_minimap_label(self, label):
		for panel_id in self.bottom_panels_dict:
			self.bottom_panels_dict[panel_id].set_minimap_label(label)

	def update_minimap_position(self):
		"""Move the minimap popover to the currently active panel."""
		btn = self.get_active_panel().get_minimap_btn()
		if btn is not None:
			self.window.minimap.set_relative_to(btn)
		else:
			self.window.minimap.set_relative_to(self.window.bottom_panel_box)

	############################################################################
	# Methods specific to the classic panel ####################################

	def get_classic_panel(self): # XXX hardcoded
		return self.bottom_panels_dict['classic']

	def left_color_btn(self):
		return self.get_classic_panel().color_popover_l

	def right_color_btn(self):
		return self.get_classic_panel().color_popover_r

	def set_palette_setting(self, show_editor):
		self.get_classic_panel().set_palette_setting(show_editor)

	def get_tool_width(self):
		return int(self.get_classic_panel().thickness_spinbtn.get_value())

	def set_right_color(self, color):
		return self.right_color_btn().color_widget.set_rgba(color)

	def set_left_color(self, color):
		return self.left_color_btn().color_widget.set_rgba(color)

	def get_right_color(self):
		return self.right_color_btn().color_widget.get_rgba()

	def get_left_color(self):
		return self.left_color_btn().color_widget.get_rgba()

	def exchange_colors(self):
		left_c = self.get_left_color()
		self.left_color_btn().color_widget.set_rgba(self.get_right_color())
		self.right_color_btn().color_widget.set_rgba(left_c)

	def get_operator(self):
		op_as_string = self.get_value('cairo_operator')
		self.get_classic_panel().set_operator(op_as_string)
		enum = self.get_classic_panel().selected_operator_enum
		label = self.get_classic_panel().selected_operator_label
		return enum, label

	############################################################################
################################################################################

