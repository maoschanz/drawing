# abstract_tool.py
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
from gi.repository import Gtk, Gdk

from .utilities_tools import utilities_show_overlay_on_context

class AbstractAbstractTool():
	"""Super-class implemented and extended by all tools."""
	__gtype_name__ = 'AbstractAbstractTool'

	def __init__(self, tool_id, label, icon_name, window, **kwargs):
		self.id = tool_id
		self.accept_selection = False
		self.use_color = False
		self.menu_id = 0
		self.label = label
		self.icon_name = icon_name
		self.tool_width = 10
		self.cursor_name = 'cell'
		self._ongoing_operation = False
		self.window = window
		self.build_row()
		self.try_build_panel()

	############################################################################
	# Actions for tool's options ###############################################

	def add_tool_action_simple(self, action_name, callback):
		"""Convenient wrapper method adding a stateless action to the window. It
		will be named 'action_name' (string) and activating the action will
		trigger the method 'callback'.""" # XXX shortcut ?
		self.window.add_action_simple(action_name, callback, None)

	def add_tool_action_boolean(self, action_name, default):
		self.window.options_manager.add_tool_option_boolean(action_name, default)

	def add_tool_action_enum(self, action_name, default):
		self.window.options_manager.add_tool_option_enum(action_name, default)

	def get_option_value(self, action_name):
		return self.window.options_manager.get_value(action_name)

	def set_action_sensitivity(self, action_name, state):
		self.get_image().set_action_sensitivity(action_name, state)

	def update_actions_state(self):
		pass

	def get_settings(self):
		return self.window._settings

	############################################################################
	# UI #######################################################################

	def show_error(self, error_text):
		self.window.prompt_message(True, error_text)

	def try_build_panel(self):
		pass

	def build_bottom_panel(self):
		return None

	def add_item_to_menu(self, tools_menu):
		tools_menu.append(self.label, 'win.active_tool::' + self.id)

	def get_options_model(self):
		fpath = '/com/github/maoschanz/drawing/tools/ui/tool_' + self.id + '.ui'
		builder = Gtk.Builder.new_from_resource(fpath)
		return builder.get_object('options-menu')

	def get_options_widget(self):
		return None

	def get_edition_status(self):
		return self.label

	def get_options_label(self):
		return _("No options")

	def build_row(self):
		"""Build the GtkRadioButton for the sidebar. This method stores it as
		'self.row', but does not pack it in the bar, and does not return it."""
		self.row = Gtk.RadioButton(relief=Gtk.ReliefStyle.NONE, \
		                        draw_indicator=False, valign=Gtk.Align.CENTER, \
		                                                tooltip_text=self.label)
		self.row.set_detailed_action_name('win.active_tool::' + self.id)
		self.label_widget = Gtk.Label(label=self.label)
		if self.get_settings().get_boolean('big-icons'):
			size = Gtk.IconSize.LARGE_TOOLBAR
		else:
			size = Gtk.IconSize.SMALL_TOOLBAR
		image = Gtk.Image().new_from_icon_name(self.icon_name, size)
		box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
		box.add(image)
		box.add(self.label_widget)
		self.row.add(box)
		self.row.show_all()

	def set_show_label(self, label_visible):
		self.label_widget.set_visible(label_visible)
		if label_visible:
			self.row.get_children()[0].set_halign(Gtk.Align.START)
		else:
			self.row.get_children()[0].set_halign(Gtk.Align.CENTER)

	def update_icon_size(self):
		image = self.row.get_children()[0].get_children()[0]
		if self.get_settings().get_boolean('big-icons'):
			size = Gtk.IconSize.LARGE_TOOLBAR
		else:
			size = Gtk.IconSize.SMALL_TOOLBAR
		image.set_from_icon_name(self.icon_name, size)

	def adapt_to_window_size(self, available_width):
		pass

	############################################################################
	# Activation or not ########################################################

	def on_tool_selected(self):
		pass

	def on_tool_unselected(self):
		pass

	def cancel_ongoing_operation(self):
		self.on_tool_unselected()
		self.give_back_control(self.accept_selection) # XXX pas sûr
		self.on_tool_selected()
		self.restore_pixbuf()
		self.non_destructive_show_modif()
		self._ongoing_operation = False

	def has_ongoing_operation(self):
		return self._ongoing_operation

	def give_back_control(self, preserve_selection):
		self.restore_pixbuf()
		self.non_destructive_show_modif()

	############################################################################
	# History ##################################################################

	def do_tool_operation(self, operation):
		if operation['tool_id'] != self.id:
			raise Exception("Can't apply operation: invalid tool id")
		self.restore_pixbuf()
		self._ongoing_operation = True

	def apply_operation(self, operation):
		self.get_image().add_pixbuf_to_history()
		self.simple_apply_operation(operation)
		self.get_image().update_actions_state()
		self.get_image().update_history_sensitivity()

	def simple_apply_operation(self, operation):
		"""Simpler apply_operation, for the 'rebuild from history' method."""
		self.do_tool_operation(operation)
		self._ongoing_operation = False
		self.get_image().add_to_history(operation)
		self.non_destructive_show_modif()

	############################################################################
	# Selection ################################################################

	def get_selection(self):
		return self.get_image().selection

	def selection_is_active(self):
		return self.get_selection().is_active

	def get_selection_pixbuf(self):
		return self.get_selection().get_pixbuf()

	def set_selection_has_been_used(self, state):
		self.get_selection().has_been_used = state

	def selection_has_been_used(self):
		return self.get_selection().has_been_used

	############################################################################
	# Image management #########################################################

	def get_image(self):
		return self.window.get_active_image()

	def get_surface(self):
		return self.get_image().get_surface()

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

	def on_motion_on_area(self, event, surface, event_x, event_y):
		pass

	def on_unclicked_motion_on_area(self, event, surface):
		pass

	def on_release_on_area(self, event, surface, event_x, event_y):
		pass

	def on_draw(self, area, cairo_context):
		if not self.accept_selection:
			return
		# Basic implementation, in fact never executed becaus tools needing it
		# will do it better to fit their needs
		if not self.selection_is_active():
			return
		self.get_selection().show_selection_on_surface(cairo_context, True, 0, 0)
		dragged_path = self.get_selection().get_path_with_scroll(0, 0)
		# XXX non, pas "0, 0", mais ce code n'est jamais exécuté normalement
		utilities_show_overlay_on_context(cairo_context, dragged_path, True)

	############################################################################
################################################################################

