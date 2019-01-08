# preferences.py
#
# Copyright 2018 Romain F. T.
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

from gi.repository import Gtk, Gio, GLib, Gdk
from .gi_composites import GtkTemplate

SETTINGS_SCHEMA = 'com.github.maoschanz.Drawing'

@GtkTemplate(ui='/com/github/maoschanz/Drawing/ui/preferences.ui')
class DrawingPrefsWindow(Gtk.Window):
	__gtype_name__ = 'DrawingPrefsWindow'

	list_box = GtkTemplate.Child()
	default_backg_button = GtkTemplate.Child()
	experimental_switch = GtkTemplate.Child()
	preview_btn = GtkTemplate.Child()
	width_btn = GtkTemplate.Child()
	height_btn = GtkTemplate.Child()
	layout_combobox = GtkTemplate.Child()
	add_alpha_switch = GtkTemplate.Child()

	_settings = Gio.Settings.new('com.github.maoschanz.Drawing')

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.init_template()
		wants_csd = not ( 'ssd' in self._settings.get_string('decorations') )
		if wants_csd:
			header_bar = Gtk.HeaderBar(visible=True, show_close_button=True, title=_("Drawing"), subtitle=_("Preferences"))
			self.set_titlebar(header_bar)

		r = float(self._settings.get_strv('default-rgba')[0])
		g = float(self._settings.get_strv('default-rgba')[1])
		b = float(self._settings.get_strv('default-rgba')[2])
		a = float(self._settings.get_strv('default-rgba')[3])
		color = Gdk.RGBA(red=r, green=g, blue=b, alpha=a)
		self.default_backg_button.set_rgba(color)
		self.default_backg_button.connect('color-set', self.on_default_backg_changed)

		self.experimental_switch.set_active(self._settings.get_boolean('experimental'))
		self.experimental_switch.connect('notify::active', self.on_experimental_changed)

		self.width_btn.set_value(self._settings.get_int('default-width'))
		self.height_btn.set_value(self._settings.get_int('default-height'))
		self.width_btn.connect('value-changed', self.on_width_changed)
		self.height_btn.connect('value-changed', self.on_height_changed)

		self.preview_btn.set_value(self._settings.get_int('preview-size'))
		self.preview_btn.connect('value-changed', self.on_preview_changed)

		self.layout_combobox.append('csd', _("Compact (headerbar)"))
		self.layout_combobox.append('ssd', _("Legacy (menubar only)"))
		self.layout_combobox.append('ssd-toolbar', _("Legacy (menubar and toolbar)"))
		if self._settings.get_boolean('experimental'):
			self.layout_combobox.append('everything', _("Both (testing only)"))
		self.layout_combobox.set_active_id(self._settings.get_string('decorations'))
		self.layout_combobox.connect('changed', self.on_layout_changed)

	def on_experimental_changed(self, w, a):
		self._settings.set_boolean('experimental', w.get_active())

	def on_default_backg_changed(self, w):
		color = self.default_backg_button.get_rgba()
		self._settings.set_strv('default-rgba', [str(color.red), str(color.green), \
			str(color.blue), str(color.alpha)])

	def on_width_changed(self, w):
		self._settings.set_int('default-width', self.width_btn.get_value())

	def on_height_changed(self, w):
		self._settings.set_int('default-height', self.height_btn.get_value())

	def on_preview_changed(self, w):
		self._settings.set_int('preview-size', self.preview_btn.get_value())

	def on_layout_changed(self, w):
		self._settings.set_string('decorations', w.get_active_id())
