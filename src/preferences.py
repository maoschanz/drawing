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

SETTINGS_SCHEMA = 'com.github.maoschanz.Draw'

@GtkTemplate(ui='/com/github/maoschanz/Draw/ui/preferences.ui')
class DrawPrefsWindow(Gtk.Window):
    __gtype_name__ = 'DrawPrefsWindow'

    reset_button = GtkTemplate.Child()
    list_box = GtkTemplate.Child()

    color_edit_switch = GtkTemplate.Child()
    default_backg_button = GtkTemplate.Child()
    experimental_switch = GtkTemplate.Child()
    width_btn = GtkTemplate.Child()
    height_btn = GtkTemplate.Child()
    layout_combobox = GtkTemplate.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init_template()
        self.list_box.set_selection_mode(Gtk.SelectionMode.NONE)

        self._settings = Gio.Settings.new(SETTINGS_SCHEMA)

        self.color_edit_switch.set_active(not self._settings.get_boolean('direct-color-edit'))
        self.color_edit_switch.connect('notify::active', self.on_color_edit_changed)

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

        self.layout_combobox.append('csd', _("Modern"))
        self.layout_combobox.append('ssd', _("Legacy"))
        self.layout_combobox.set_active_id(self._settings.get_string('decorations'))
        self.layout_combobox.connect('changed', self.on_layout_changed)

# TODO :
# le reset

    def on_color_edit_changed(self, w, a):
        self._settings.set_boolean('direct-color-edit', not w.get_active())

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

    def on_layout_changed(self, w):
        self._settings.set_string('decorations', w.get_active_id())
