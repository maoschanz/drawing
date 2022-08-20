# abstract_tool.py
#
# Copyright 2018-2022 Romain F. T.
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
from gi.repository import Gtk, Gdk

class WrongToolIdException(Exception):
	def __init__(self, expected, actual):
		# Context: an error message
		msg = _("Can't start operation: wrong tool id (expected {0}, got {1})")
		super().__init__(msg.format(expected, actual))

################################################################################

class AbstractAbstractTool():
	"""Super-class implemented and extended by all tools."""

	__gtype_name__ = 'AbstractAbstractTool'
	UI_PATH = '/com/github/maoschanz/drawing/tools/ui/'

	def __init__(self, tool_id, label, icon_name, window, **kwargs):
		self.window = window
		# The tool's identity
		self.id = tool_id
		self.menu_id = 0
		self.label = self._mnemo_label = label
		self._mnemo_char = ""
		self._icon_name = icon_name
		# The options it supports
		self.accept_selection = False
		self.use_color = False
		self.use_operator = False
		# The tool's state
		self.cursor_name = 'cell'
		self._ongoing_operation = False
		self._modifier_keys = []
		# Once everything is set, build the UI
		self.try_build_pane()

	############################################################################
	# Utilities managing actions for tool's options ############################

	def add_tool_action_simple(self, action_name, callback):
		"""Convenient wrapper method adding a stateless action to the window. It
		will be named 'action_name' (string) and activating the action will
		trigger the method 'callback'."""
		# XXX allow to set shortcuts here?
		self.window.add_action_simple(action_name, callback)

	def add_tool_action_boolean(self, action_name, default):
		self.window.options_manager.add_option_boolean(action_name, default)

	def add_tool_action_enum(self, action_name, default):
		self.window.options_manager.add_option_enum(action_name, default)

	def load_tool_action_boolean(self, action_name, key_name):
		om = self.window.options_manager
		return om.add_option_from_bool_key(action_name, key_name)

	def load_tool_action_enum(self, action_name, key_name):
		om = self.window.options_manager
		return om.add_option_from_enum_key(action_name, key_name)

	def get_option_value(self, action_name):
		return self.window.options_manager.get_value(action_name)

	def set_action_sensitivity(self, action_name, state):
		self.window.lookup_action(action_name).set_enabled(state)

	def update_actions_state(self):
		self.set_action_sensitivity('main_color', self.use_color)
		self.set_action_sensitivity('secondary_color', self.use_color)
		self.set_action_sensitivity('exchange_color', self.use_color)
		self.set_action_sensitivity('cairo_operator', self.use_operator)

		self.set_action_sensitivity('cancel_transform', False)
		self.set_action_sensitivity('apply_transform', False)

	def get_settings(self):
		return self.window.options_manager._tools_gsettings

	def update_modifier_state(self, event_state):
		modifier_keys = []
		# CONTROL_MASK can't be used, because it already has an effect app-wide.
		if (event_state & Gdk.ModifierType.SHIFT_MASK) == Gdk.ModifierType.SHIFT_MASK:
			modifier_keys.append('SHIFT')
		if (event_state & Gdk.ModifierType.MOD1_MASK) == Gdk.ModifierType.MOD1_MASK:
			modifier_keys.append('ALT')
		self._modifier_keys = modifier_keys

	############################################################################
	# Various utilities ########################################################

	def show_error(self, error_text):
		self.window.reveal_message(error_text)

	def get_tooltip(self, event_x, event_y, motion_behavior):
		return None

	############################################################################
	# Bottom pane and menubar integration ######################################

	def try_build_pane(self):
		pass

	def build_bottom_pane(self):
		return None

	def on_apply_transform_tool_operation(self, *args):
		pass # implemented only by transform tools

	def on_cancel_transform_tool_operation(self, *args):
		pass # implemented only by transform tools

	def get_options_label(self):
		return _("No options")

	def adapt_to_window_size(self, available_width):
		pass

	def add_item_to_menu(self, tools_menu):
		tools_menu.append(self._mnemo_label, 'win.active_tool::' + self.id)

	def get_options_model(self):
		"""Returns a Gio.MenuModel corresponding to the tool's options. It'll be
		shown in the menubar (if any) and in the bottom pane (if the tool's
		bottom pane supports such a feature)."""
		fpath = self.UI_PATH + 'tool-' + self.id + '.ui'
		builder = Gtk.Builder.new_from_resource(fpath)
		return builder.get_object('options-menu')

	def get_options_widget(self):
		"""Returns a Gtk.Widget (normally a box) corresponding to the tool's
		options. It'll be in the bottom pane (if the tool's bottom pane supports
		such a feature) in replacement of the Gio.MenuModel if such a simple
		menu can't provide all the features."""
		return None

	def get_editing_tips(self):
		return [self.label]

	############################################################################
	# Side pane ################################################################

	def set_mnemonics(self, character):
		self._mnemo_label = self.label.replace(character, "_" + character, 1)
		self._mnemo_char = character.upper()

	def build_flowbox_child(self, flowbox):
		"""Build the icon and its label for the sidebar."""
		# The icon
		if self.window.gsettings.get_boolean('big-icons'):
			size = Gtk.IconSize.LARGE_TOOLBAR
		else:
			size = Gtk.IconSize.SMALL_TOOLBAR
		image = Gtk.Image().new_from_icon_name(self._icon_name, size)
		self._label_box = Gtk.Box( \
			orientation=Gtk.Orientation.HORIZONTAL, \
			spacing=8, \
			margin=8 \
		)
		self._label_box.add(image)

		# The readable label
		label_widget = Gtk.Label(use_underline=True, label=self._mnemo_label)
		self._label_box.add(label_widget)
		self._label_box.show_all()

		# The "mini-label" is shown only when pressing <Alt>
		mini_label = Gtk.Label(use_underline=True, label="_" + self._mnemo_char)
		self._label_box.add(mini_label)

		flowbox.add(self._label_box)
		self._fb_child = self._label_box.get_parent()

		# The item's tooltip
		if self._mnemo_char == "":
			self._fb_child.set_tooltip_text(self.label)
		else:
			tooltip = self.label + " (Alt+" + self._mnemo_char + ")"
			self._fb_child.set_tooltip_text(tooltip)

	def select_flowbox_child(self, *args):
		self.window.tools_flowbox.select_child(self._fb_child)

	def is_flowbox_child_selected(self):
		return self._fb_child.is_selected()

	def set_show_label(self, label_visible):
		label_widget = self._label_box.get_children()[1]
		label_widget.set_visible(label_visible)
		icon = self._label_box.get_children()[0]
		if label_visible:
			icon.set_halign(Gtk.Align.START)
		else:
			icon.set_halign(Gtk.Align.CENTER)

	def update_icon_size(self):
		image = self._label_box.get_children()[0]
		if self.window.gsettings.get_boolean('big-icons'):
			size = Gtk.IconSize.LARGE_TOOLBAR
		else:
			size = Gtk.IconSize.SMALL_TOOLBAR
		image.set_from_icon_name(self._icon_name, size)

	def show_only_mnemonics(self, should_show):
		if self._mnemo_char == "":
			return
		label_widget = self._label_box.get_children()[1]
		if label_widget.get_visible():
			return
		image = self._label_box.get_children()[0]
		mini_label = self._label_box.get_children()[2]

		image.set_visible(not should_show)
		mini_label.set_visible(should_show)

	############################################################################
	# Activation or not ########################################################

	def on_tool_selected(self):
		pass

	def on_tool_unselected(self):
		pass

	def cancel_ongoing_operation(self):
		"""Reset the current tool when 'undo' is pressed while an operation has
		been started but not applied."""
		self.on_tool_unselected()
		self.give_back_control(self.accept_selection)
		self.on_tool_selected()
		self.restore_pixbuf()
		self.non_destructive_show_modif()
		self._ongoing_operation = False

	def give_back_control(self, preserve_selection):
		self.restore_pixbuf()
		self.non_destructive_show_modif()

	############################################################################
	# History ##################################################################

	def has_ongoing_operation(self):
		return self._ongoing_operation

	def do_tool_operation(self, operation):
		pass

	def start_tool_operation(self, operation):
		if operation['tool_id'] != self.id:
			raise WrongToolIdException(operation['tool_id'], self.id)
		self.restore_pixbuf()
		self._ongoing_operation = True

	def apply_operation(self, operation):
		"""Complete method to apply an operation: the operation is applied and
		the image is updated as well as the state of actions."""
		self.simple_apply_operation(operation)
		self.get_image().update_actions_state()
		self.get_image().update_history_sensitivity()

	def simple_apply_operation(self, operation):
		"""Simpler apply_operation, for the 'rebuild from history' method."""
		try:
			self.do_tool_operation(operation)
			self.get_image().add_to_history(operation)
		except Exception as e:
			self.show_error(str(e))
		self._ongoing_operation = False
		self.non_destructive_show_modif() # XXX nécessaire ?

	############################################################################
	# Selection ################################################################

	def get_selection(self):
		return self.get_image().selection

	def selection_is_active(self):
		return self.get_selection().is_active

	def get_selection_pixbuf(self):
		return self.get_selection().get_pixbuf()

	def get_overlay_thickness(self):
		return (1 / self.get_image().zoom_level)

	############################################################################
	# Image management #########################################################

	def get_image(self):
		return self.window.get_active_image()

	def get_surface(self):
		return self.get_image().get_surface()

	def scale_factor(self):
		return self.get_image().SCALE_FACTOR

	def get_context(self):
		return cairo.Context(self.get_surface())

	def get_main_pixbuf(self):
		return self.get_image().main_pixbuf

	def non_destructive_show_modif(self):
		self.get_image().update()

	def restore_pixbuf(self):
		self.get_image().use_stable_pixbuf()

	############################################################################
	# Signals handling #########################################################

	def on_press_on_area(self, event, surface, event_x, event_y):
		pass

	def on_motion_on_area(self, event, surface, event_x, event_y, render=True):
		pass

	def on_unclicked_motion_on_area(self, event, surface):
		pass

	def on_release_on_area(self, event, surface, event_x, event_y):
		pass

	def on_draw_above(self, area, cairo_context):
		pass

	############################################################################
################################################################################

