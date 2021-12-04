# optionsbar_color_popover.py
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
from gi.repository import Gtk
from .utilities import utilities_get_rgba_name

PREFIX = '/com/github/maoschanz/drawing/'

CAIRO_OP_VALUES = {
	'over': cairo.Operator.OVER,
	'clear': cairo.Operator.CLEAR,

	'source': cairo.Operator.SOURCE,
	'difference': cairo.Operator.DIFFERENCE,

	# "Highlight" submenu
	'multiply': cairo.Operator.MULTIPLY,
	'screen': cairo.Operator.SCREEN,

	'hsl-hue': cairo.Operator.HSL_HUE,
	'hsl-saturation': cairo.Operator.HSL_SATURATION,
	'hsl-color': cairo.Operator.HSL_COLOR,
	'hsl-luminosity': cairo.Operator.HSL_LUMINOSITY,
}

CAIRO_OP_LABELS = {
	'over': _("Normal"),
	'clear': _("Erase"),

	'source': _("Raw source color"),
	'difference': _("Difference"),

	'multiply': _("Highlight"),
	# Context: this is equivalent to "Highlight: Light text on dark background"
	# but it has to be FAR SHORTER so it fits in the color chooser
	'screen': _("Highlight (dark)"),

	'hsl-hue': _("Hue only"),
	'hsl-saturation': _("Saturation only"),
	'hsl-color': _("Hue and saturation"),
	'hsl-luminosity': _("Luminosity only"),
}

################################################################################

class OptionsBarClassicColorPopover(Gtk.Popover):
	__gtype_name__ = 'OptionsBarClassicColorPopover'

	def __init__(self, btn, thumbn, is_left_color, options_manager):
		super().__init__()

		suffix = 'optionsbars/classic/optionsbar-color-popover.ui'
		builder = Gtk.Builder.new_from_resource(PREFIX + suffix)

		main_box = builder.get_object('main-box')
		self.add(main_box)
		self._button = btn
		self._button.set_popover(self)
		self._thumbnail_image = thumbn
		self._options_manager = options_manager

		# These attributes are the same in both oppovers, but this may evolve
		self._operator_enum = cairo.Operator.OVER
		self._operator_label = _("Normal")

		########################################################################
		# Box at the top #######################################################

		if is_left_color:
			title_label = _("Main color")
		else:
			title_label = _("Secondary color")
		self._popover_title = builder.get_object('popover-title')
		self._popover_title.set_label(title_label)

		self._operator_box_1 = builder.get_object('operator-box-start')
		self._operator_box_2 = builder.get_object('operator-box-end')

		operators_radio_group = builder.get_object('op-group')
		self._build_all_operators_groups(operators_radio_group)

		########################################################################
		# Color chooser widget #################################################

		self.color_widget = builder.get_object('color-widget')
		initial_rgba = self._options_manager.get_persisted_color(is_left_color)
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

	def _build_all_operators_groups(self, radio_group):
		self._operators_menus = []
		self._operators_hideable_radiobtns = {
			'over': None,
			'erase': None,
		}
		suffix = 'optionsbars/classic/optionsbar-operator-menus.ui'
		builder = Gtk.Builder.new_from_resource(PREFIX + suffix)

		box = self._build_radios(radio_group, ['multiply', 'screen'])
		menu_model = builder.get_object('highlight-operators-menu')
		btn = self._build_op_menu(menu_model, 'tool-highlight-symbolic')
		btn.set_tooltip_text(_("Highlight"))
		box.add(btn)
		self._operator_box_1.add(box)

		box = self._build_radios(radio_group, ['hsl-hue', 'hsl-saturation',
		                                       'hsl-color', 'hsl-luminosity'])
		menu_model = builder.get_object('hsl-operators-menu')
		btn = self._build_op_menu(menu_model, 'display-brightness-symbolic')
		btn.set_tooltip_text(_("HSL modes"))
		box.add(btn)
		self._operator_box_1.add(box)

		box = self._build_radios(radio_group, ['source', 'difference'])
		menu_model = builder.get_object('other-operators-menu')
		btn = self._build_op_menu(menu_model, 'view-more-symbolic')
		btn.set_tooltip_text(_("Other modes"))
		box.add(btn)
		self._operator_box_1.add(box)

	def _build_radios(self, radio_group, ops_list):
		groupbox = Gtk.Box(visible=True)
		groupbox.get_style_context().add_class('linked')
		for operator_id in ops_list:
			button = Gtk.RadioButton(visible=False, draw_indicator=False)
			button.join_group(radio_group)
			button.set_detailed_action_name ('win.cairo_op_mirror::' + operator_id)

			# To avoid buttons bigger than the popover the label is ellipsized
			button_label = CAIRO_OP_LABELS[operator_id]
			if len(button_label) > 16:
				button.set_tooltip_text(button_label)
				button_label = button_label[:14] + "…"
			button.set_label(button_label)

			self._operators_hideable_radiobtns[operator_id] = button
			groupbox.add(button)
		return groupbox

	def _build_op_menu(self, menu_model, icon_name):
		menu_btn = Gtk.MenuButton(visible=True)
		image = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
		menu_btn.set_image(image)
		menu_btn.set_menu_model(menu_model)
		self._operators_menus.append(menu_btn.get_popover())
		return menu_btn

	############################################################################

	def set_operators_available(self, tool_use_operator, op_as_string):
		"""Adapts the availability of operators to the tool's property."""
		self._operator_box_1.set_visible(tool_use_operator)
		self._operator_box_2.set_visible(tool_use_operator)
		self._popover_title.set_visible(not tool_use_operator)
		self.adapt_to_operator(op_as_string)

	def _operator_supports_color(self, op_as_string):
		return not op_as_string == 'clear'

	def adapt_to_operator(self, op_as_string):
		self._operator_enum = CAIRO_OP_VALUES[op_as_string]
		self._operator_label = CAIRO_OP_LABELS[op_as_string]
		# print("adapt to operator :", op_as_string)
		supports_colors = self._operator_supports_color(op_as_string)

		# Close all little menus
		for op_submenu in self._operators_menus:
			op_submenu.popdown()

		# Show only the radio button for the active operator
		for operator_id in self._operators_hideable_radiobtns:
			op_radiobtn = self._operators_hideable_radiobtns[operator_id]
			if op_radiobtn is not None:
				op_radiobtn.set_visible(operator_id == op_as_string)

		self.color_widget.set_sensitive(supports_colors)
		self._set_thumbnail_color(op_as_string)

	def _on_color_changed(self, *args):
		"""When the use clicks on a color in the palette"""
		op_as_string = self._options_manager.get_value('cairo_operator')
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
			tooltip_string = self._operator_label
		elif op_as_string == 'over':
			pass # Normal situation, no need to tell the user
		else:
			tooltip_string = self._operator_label + ' - ' + tooltip_string
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

