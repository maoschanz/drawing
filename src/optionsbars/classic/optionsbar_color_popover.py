# panel_classic_color_popover.py
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

	def __init__(self, btn, thumbn, initial_rgba, is_main_c, window, **kwargs):
		super().__init__(**kwargs) # TODO passer l'options_manager, pas la window

		suffix = 'optionsbars/classic/optionsbar-color-popover.ui'
		builder = Gtk.Builder.new_from_resource(PREFIX + suffix)

		main_box = builder.get_object('main-box')
		self.add(main_box)
		self._button = btn
		self._button.set_popover(self)
		self._thumbnail_image = thumbn
		self.window = window

		########################################################################
		# Box at the top #######################################################

		if is_main_c:
			title_label = _("Main color")
		else:
			title_label = _("Secondary color")
		builder.get_object('popover-title').set_label(title_label)

		self._operator_menu_btn = builder.get_object('operator-menu-btn')
		builder.add_from_resource(PREFIX + 'ui/app-menus.ui')
		operator_menu_model = builder.get_object('operator-menu')
		self._operator_menu_btn.set_menu_model(operator_menu_model)

		self._operator_label = builder.get_object('operator-label')
		self.window.options_manager.add_tool_option_enum('cairo_operator', 'over')

		########################################################################
		# Color chooser widget #################################################

		r = float(initial_rgba[0])
		g = float(initial_rgba[1])
		b = float(initial_rgba[2])
		a = float(initial_rgba[3])
		initial_rgba = Gdk.RGBA(red=r, green=g, blue=b, alpha=a)

		self.color_widget = builder.get_object('color-widget')
		self.color_widget.set_rgba(initial_rgba)
		self.color_widget.connect('notify::rgba', self._set_thumbail_color)
		self.color_widget.connect('notify::show-editor', self._update_nav_box)

		########################################################################
		# Navigation box at the bottom #########################################

		back_btn = builder.get_object('back-btn')
		self.editor_box = builder.get_object('editor-box')
		back_btn.connect('clicked', self._close_color_editor)

		self._update_nav_box()
		self._set_thumbail_color()
		# self.update_mode() # XXX pas possible, on est en train de construire
		             # le panneau on ne peut pas appeler l'option manager dessus

	############################################################################

	def update_mode(self):
		self._operator_menu_btn.set_active(False)
		operator_str = self.window.options_manager.get_operator()[1]
		self._operator_label.set_label(operator_str)

	def _set_thumbail_color(self, *args):
		"""Update the 'rgba' property of the GtkColorWidget and its preview."""
		surface = cairo.ImageSurface(cairo.Format.ARGB32, 16, 16)
		cairo_context = cairo.Context(surface)
		rgba = self.color_widget.get_rgba()
		red = rgba.red
		green = rgba.green
		blue = rgba.blue
		alpha = rgba.alpha
		cairo_context.set_source_rgba(red, green, blue, alpha)
		cairo_context.paint()
		self._thumbnail_image.set_from_surface(surface)
		# TODO mettre le mode aussi
		tooltip_string = utilities_get_rgba_name(red, green, blue, alpha)
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

