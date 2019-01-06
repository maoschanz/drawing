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

from .window import DrawingWindow
from .preferences import DrawingPrefsWindow

class Application(Gtk.Application):
	about_dialog = None
	shortcuts_window = None
	prefs_window = None

	def __init__(self, version):
		super().__init__(application_id='com.github.maoschanz.Drawing',
						flags=Gio.ApplicationFlags.HANDLES_OPEN)

		GLib.set_application_name('Drawing')
		GLib.set_prgname('com.github.maoschanz.Drawing')
		self.register(None) # ?
		self.version = version

		if not self.get_is_remote():
			self.on_startup()

		self.add_main_option('version', b'v', GLib.OptionFlags.NONE,
							GLib.OptionArg.NONE, "Version", None)

		self.connect('open', self.on_open_from_cli)
		self.connect('handle-local-options', self.on_local_options)

	def on_startup(self):
		self.build_actions()
		self.add_accels()
		menubar_model = self.build_menubar()
		self.set_menubar(menubar_model)
		self.has_tools_in_menubar = False
		if self.prefers_app_menu():
			appmenu_model = self.build_app_menu()
			self.set_app_menu(appmenu_model)

	def on_open_from_cli(self, a, b, c, d):
		for f in b:
			win = self.on_new_window_activate()
			win.try_load_file(f.get_path())
		return 0

	def on_local_options(self, app, options):
		if options.contains('version'):
			print("Drawing %s" % self.version)
			exit(0)
		return -1

	def build_about_dialog(self):
		self.about_dialog = Gtk.AboutDialog.new()
		self.about_dialog.set_comments(_("A drawing application for the GNOME desktop."))
		self.about_dialog.set_authors(['Romain F. T.'])
		self.about_dialog.set_copyright('© 2018 Romain F. T.')
		self.about_dialog.set_license_type(Gtk.License.GPL_3_0)
		self.about_dialog.set_logo_icon_name('com.github.maoschanz.Drawing')
		self.about_dialog.set_version(str(self.version))
		self.about_dialog.set_website('github.com/maoschanz/drawing')
		self.about_dialog.set_website_label(_("Report bugs or ideas"))

	def build_shortcuts_dialog(self):
		builder = Gtk.Builder().new_from_resource('/com/github/maoschanz/Drawing/ui/shortcuts.ui')
		self.shortcuts_window = builder.get_object('shortcuts')

	def build_app_menu(self):
		builder = Gtk.Builder()
		builder.add_from_resource('/com/github/maoschanz/Drawing/ui/menus.ui')
		appmenu = builder.get_object('app-menu')
		return appmenu

	def build_menubar(self):
		builder = Gtk.Builder()
		builder.add_from_resource('/com/github/maoschanz/Drawing/ui/menus.ui')
		menubar = builder.get_object('menu-bar')
		return menubar

	def add_action_simple(self, action_name, callback):
		action = Gio.SimpleAction.new(action_name, None)
		action.connect('activate', callback)
		self.add_action(action)

	def add_action_boolean(self, action_name, default, callback):
		action = Gio.SimpleAction().new_stateful(action_name, None, \
			GLib.Variant.new_boolean(default))
		action.connect('change-state', callback)
		self.add_action(action)

	def build_actions(self):
		self.add_action_simple('new_window', self.on_new_window_activate)
		self.add_action_simple('open', self.on_open_activate)
		self.add_action_simple('settings', self.on_prefs_activate)
		self.add_action_simple('shortcuts', self.on_shortcuts_activate)
		self.add_action_simple('help', self.on_help_activate)
		self.add_action_simple('about', self.on_about_activate)
		self.add_action_simple('quit', self.on_quit)

	def add_accels(self):
		self.set_accels_for_action('app.new_window', ['<Ctrl>n'])
		self.set_accels_for_action('app.open', ['<Ctrl>o'])
		self.set_accels_for_action('app.help', ['F1'])
		self.set_accels_for_action('app.quit', ['<Ctrl>q'])

		# TODO mettre à jour la fentre qui résume ça
		self.set_accels_for_action('win.main_color', ['<Ctrl>l'])
		self.set_accels_for_action('win.secondary_color', ['<Ctrl>r'])
		self.set_accels_for_action('win.exchange_color', ['<Ctrl>e'])

		self.set_accels_for_action('win.import', ['<Ctrl>i'])
		self.set_accels_for_action('win.paste', ['<Ctrl>v'])
		self.set_accels_for_action('win.select_all', ['<Ctrl>a'])

		self.set_accels_for_action('win.selection_unselect', ['<Ctrl>u'])
		self.set_accels_for_action('win.selection_cut', ['<Ctrl>x'])
		self.set_accels_for_action('win.selection_copy', ['<Ctrl>c'])
		self.set_accels_for_action('win.selection_delete', ['<Ctrl>Delete'])

		self.set_accels_for_action('win.main_menu', ['F10'])
		self.set_accels_for_action('win.toggle_preview', ['<Ctrl>m'])

		self.set_accels_for_action('win.properties', ['<Ctrl>p'])

		self.set_accels_for_action('win.close', ['<Ctrl>w'])
		self.set_accels_for_action('win.save', ['<Ctrl>s'])
		self.set_accels_for_action('win.save_as', ['<Ctrl><Shift>s'])

		self.set_accels_for_action('win.undo', ['<Ctrl>z'])
		self.set_accels_for_action('win.redo', ['<Ctrl><Shift>z'])

	def on_about_activate(self, *args):
		if self.about_dialog is None:
			self.build_about_dialog()
		else:
			self.about_dialog.destroy()
			self.build_about_dialog()
		self.about_dialog.show()

	def on_quit(self, *args):
		self.quit()

	def on_new_window_activate(self, *args):
		win = DrawingWindow(application=self)
		win.present()
		return win

	def on_open_activate(self, *args):
		win = self.on_new_window_activate()
		win.action_open()

	def on_shortcuts_activate(self, *args):
		if self.shortcuts_window is not None:
			self.shortcuts_window.destroy()
		self.build_shortcuts_dialog()
		self.shortcuts_window.present()

	def on_prefs_activate(self, *args):
		if self.prefs_window is not None:
			self.prefs_window.destroy()
		self.prefs_window = DrawingPrefsWindow()
		self.prefs_window.present()

	def on_help_activate(self, *args):
		Gtk.show_uri(None, 'help:drawing', Gdk.CURRENT_TIME)

	def do_activate(self):
		win = self.props.active_window
		if not win:
			self.on_startup()
			self.on_new_window_activate()
		else:
			win.present()

def main(version):
	app = Application(version)
	return app.run(sys.argv)
