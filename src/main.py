# main.py
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import sys
import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gio, GLib, Gdk

from .window import DrawWindow
from .preferences import DrawPrefsWindow

class Application(Gtk.Application):

	def __init__(self):
		super().__init__(application_id='com.github.maoschanz.Draw',
						flags=Gio.ApplicationFlags.HANDLES_OPEN)

		GLib.set_application_name('Draw')
		GLib.set_prgname('com.github.maoschanz.Draw')

		self.register(None) # ?

		menu = self.build_app_menu()
		if self.prefers_app_menu():
			self.set_app_menu(menu)

		self.version = 'beta-2018-11-10' # TODO

		self.connect('open', self.on_open)

	def on_open(self, a, b, c, d):
		for f in b:
			win = DrawWindow(f.get_path(), application=self)
			win.present()
		return 0

	def build_about_dialog(self):
		self.about_dialog = Gtk.AboutDialog.new()
		self.about_dialog.set_comments(_("A drawing application for the GNOME desktop."))
		self.about_dialog.set_authors(['Romain F. T.'])
		self.about_dialog.set_copyright('© 2018 Romain F. T.')
		self.about_dialog.set_license_type(Gtk.License.GPL_3_0)
		self.about_dialog.set_logo_icon_name('com.github.maoschanz.Draw')
		self.about_dialog.set_version(str(self.version))
		self.about_dialog.set_website('github.com/maoschanz/draw')
		self.about_dialog.set_website_label(_("Report bugs or ideas"))

	def build_shortcuts_dialog(self):
		builder = Gtk.Builder().new_from_resource('/com/github/maoschanz/Draw/ui/shortcuts.ui')
		self.shortcuts_window = builder.get_object('shortcuts')
		self.shortcuts_window.present()

	def build_app_menu(self):
		builder = Gtk.Builder()
		builder.add_from_resource("/com/github/maoschanz/Draw/ui/menus.ui")
		menu = builder.get_object("app-menu")

		new_window_action = Gio.SimpleAction.new("new_window", None) # FIXME
		new_window_action.connect("activate", self.on_new_window_activate)
		self.add_action(new_window_action)

		prefs_action = Gio.SimpleAction.new("settings", None)
		prefs_action.connect("activate", self.on_prefs_activate)
		self.add_action(prefs_action)

		shortcuts_action = Gio.SimpleAction.new("shortcuts", None)
		shortcuts_action.connect("activate", self.on_shortcuts_activate)
		self.add_action(shortcuts_action)

		help_action = Gio.SimpleAction.new("help", None)
		help_action.connect("activate", self.on_help_activate)
		self.add_action(help_action)

		about_action = Gio.SimpleAction.new("about", None)
		about_action.connect("activate", self.on_about_activate)
		self.add_action(about_action)

		quit_action = Gio.SimpleAction.new("quit", None)
		quit_action.connect("activate", self.on_quit)
		self.add_action(quit_action)

		self.set_accels_for_action("app.new_window", ["<Ctrl>n"])
		self.set_accels_for_action("app.quit", ["<Ctrl>q"])

		self.set_accels_for_action("win.paste", ["<Ctrl>v"])
		self.set_accels_for_action("win.select_all", ["<Ctrl>a"])
		self.set_accels_for_action("win.unselect", ["<Ctrl>u"])

		self.set_accels_for_action("win.properties", ["<Ctrl>p"])
		self.set_accels_for_action("win.close", ["<Ctrl>w"])
		self.set_accels_for_action("win.save", ["<Ctrl>s"])
		self.set_accels_for_action("win.open", ["<Ctrl>o"])

		self.set_accels_for_action("win.undo", ["<Ctrl>z"])
		self.set_accels_for_action("win.redo", ["<Ctrl><Shift>z"])

		return menu

	def on_about_activate(self, *args):
		self.build_about_dialog()
		self.about_dialog.show()

	def on_quit(self, *args):
		self.quit()

	def on_new_window_activate(self, *args):
		win = DrawWindow(None, application=self)
		win.present()

	def on_shortcuts_activate(self, *args):
		self.build_shortcuts_dialog()
		self.shortcuts_dialog.show_all()

	def on_prefs_activate(self, *args):
		self.prefs_window = DrawPrefsWindow()
		self.prefs_window.present()

	def on_help_activate(self, *args):
		Gtk.show_uri(None, "help:draw", Gdk.CURRENT_TIME)

	def do_activate(self):
		win = self.props.active_window
		if not win:
			win = DrawWindow(None, application=self)
		win.present()

def main(version):
	app = Application()
	return app.run(sys.argv)
