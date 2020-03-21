# optionsbar_color_popover.py
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
from .utilities import utilities_get_rgba_name

PREFIX = '/com/github/maoschanz/drawing/'

class OptionsBarClassicColorPopover(Gtk.Popover):
	__gtype_name__ = 'OptionsBarClassicColorPopover'

	def __init__(self, btn, thumbn, initial_rgba, is_main_c, cl_bar, **kwargs):
		super().__init__(**kwargs)

		suffix = 'optionsbars/classic/optionsbar-color-popover.ui'
		builder = Gtk.Builder.new_from_resource(PREFIX + suffix)

		main_box = builder.get_object('main-box')
		self.add(main_box)
		self._button = btn
		self._button.set_popover(self)
		self._thumbnail_image = thumbn
		self._parent_bar = cl_bar

		########################################################################
		# Box at the top #######################################################

		if is_main_c:
			title_label = _("Main color")
		else:
			title_label = _("Secondary color")
		self._popover_title = builder.get_object('popover-title')
		self._popover_title.set_label(title_label)

		self._operator_box_1 = builder.get_object('operator-box-start')
		self._operator_box_2 = builder.get_object('operator-box-end')

		########################################################################
		# Color chooser widget #################################################

		r = float(initial_rgba[0])
		g = float(initial_rgba[1])
		b = float(initial_rgba[2])
		a = float(initial_rgba[3])
		initial_rgba = Gdk.RGBA(red=r, green=g, blue=b, alpha=a)

		self.color_widget = builder.get_object('color-widget')
		self.color_widget.set_rgba(initial_rgba)
		self.color_widget.connect('notify::rgba', self._on_color_changed)
		self.color_widget.connect('notify::show-editor', self._update_nav_box)

		########################################################################
		# Navigation box at the bottom #########################################

		back_btn = builder.get_object('back-btn')
		self.editor_box = builder.get_object('editor-box')
		back_btn.connect('clicked', self._close_color_editor)

		self._update_nav_box()
		self._on_color_changed()

	############################################################################

	def set_operators_available(self, tool_use_operator, op_as_string):
		"""Adapts the availability of operators to the tool's property."""
		self._operator_box_1.set_visible(tool_use_operator)
		self._operator_box_2.set_visible(tool_use_operator)
		self._popover_title.set_visible(not tool_use_operator)
		self.adapt_to_operator(op_as_string)

	def _operator_supports_color(self, op_as_string):
		return not (op_as_string == 'clear' or op_as_string == 'dest_in')

	def adapt_to_operator(self, op_as_string):
		supports_colors = self._operator_supports_color(op_as_string)
		self.color_widget.set_sensitive(supports_colors)
		self._set_thumbnail_color(op_as_string)

	def _on_color_changed(self, *args):
		"""When the use clicks on a color in the palette"""
		op_as_string = self._parent_bar.window.options_manager.get_value( \
		                                                       'cairo_operator')
		self._set_thumbnail_color(op_as_string)

	def _set_thumbnail_color(self, op_as_string):
		"""Sets the icon and the tooltip of the popover's button. The icon can
		be an actual icon, or a rectangle of color. The tooltip shows the active
		operator (if pertinent), and an approximation of the color name (if
		pertinent)."""
		rgba = self.color_widget.get_rgba()
		red = rgba.red
		green = rgba.green
		blue = rgba.blue
		alpha = rgba.alpha

		# Draw the thumbnail of the button
		if op_as_string == 'clear':
			self._thumbnail_image.set_from_icon_name('tool-eraser-symbolic', \
			                                         Gtk.IconSize.SMALL_TOOLBAR)
		elif op_as_string == 'dest_in': # blur
			self._thumbnail_image.set_from_icon_name('mode-blur-symbolic', \
			                                         Gtk.IconSize.SMALL_TOOLBAR)
		else:
			surface = cairo.ImageSurface(cairo.Format.ARGB32, 16, 16)
			cairo_context = cairo.Context(surface)
			cairo_context.set_source_rgba(red, green, blue, alpha)
			cairo_context.paint()
			# it could explicit whether it's normal/source/difference
			self._thumbnail_image.set_from_surface(surface)

		# Set the tooltip of the button
		tooltip_string = utilities_get_rgba_name(red, green, blue, alpha)
		if not self._operator_supports_color(op_as_string):
			# FIXME not if the tool is the eraser
			tooltip_string = self._parent_bar._operator_label
		elif op_as_string == 'over':
			pass # Normal situation, no need to tell the user
		else:
			# XXX shouldn't fail but is ugly
			tooltip_string = self._parent_bar._operator_label + ' — ' + tooltip_string
		self._button.set_tooltip_text(tooltip_string)

	############################################################################

	def editor_setting_changed(self, show_editor):
		self.color_widget.props.show_editor = show_editor
		self._update_nav_box()

	def _close_color_editor(self, *args):
		self.color_widget.props.show_editor = False

	def open(self, *args):
		self._button.activate()

	def _update_nav_box(self, *args):
		"""Update the visibility of navigation controls ('back to the palette'
		and 'always use this editor')."""
		self.editor_box.set_visible(self.color_widget.props.show_editor)

	############################################################################
################################################################################

