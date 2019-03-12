# main.py
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import sys, gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gio, GLib, Gdk

from .window import DrawingWindow
from .preferences import DrawingPrefsWindow

APP_ID = 'com.github.maoschanz.Drawing'

def main(version):
	app = Application(version)
	return app.run(sys.argv)

################################################################################

class Application(Gtk.Application):
	about_dialog = None
	shortcuts_window = None
	prefs_window = None

	def __init__(self, version):
		super().__init__(application_id=APP_ID,
		                 flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)

		GLib.set_application_name('Drawing')
		GLib.set_prgname(APP_ID)
		self.version = version
		self.git_url = 'https://github.com/maoschanz/drawing'
		self.has_tools_in_menubar = False

		self.connect('startup', self.on_startup)
		self.register(None)

		self.connect('activate', self.on_activate)
		self.connect('command-line', self.on_cli)

		self.add_main_option('version', b'v', GLib.OptionFlags.NONE,
		                     GLib.OptionArg.NONE,
		                     _("Print the version and display the 'about' dialog"),
		                     None)
		self.add_main_option('new-window', b'n', GLib.OptionFlags.NONE,
		                     GLib.OptionArg.NONE, _("Open a new window"), None)
		self.add_main_option('new-tab', b't', GLib.OptionFlags.NONE,
		                     GLib.OptionArg.NONE, _("Open a new tab"), None)

		icon_theme = Gtk.IconTheme.get_default()
		icon_theme.add_resource_path('/com/github/maoschanz/Drawing/icons')
		icon_theme.add_resource_path('/com/github/maoschanz/Drawing/tools/icons')

########

	def on_startup(self, *args):
		"""Add app-wide menus and actions, and all accels."""
		self.build_actions()
		self.add_accels()
		builder = Gtk.Builder.new_from_resource( \
		                        '/com/github/maoschanz/Drawing/ui/app-menus.ui')
		menubar_model = builder.get_object('menu-bar')
		self.set_menubar(menubar_model)
		if self.prefers_app_menu():
			appmenu_model = builder.get_object('app-menu')
			self.set_app_menu(appmenu_model)

	def is_beta(self):
		"""Tells is the app version is even or odd, odd versions being considered
		as unstable versions. This affects available options and the style of
		the headerbar."""
		version_array = self.version.split('.')
		if int(version_array[1]) * 5 == 5:
			return True
		else:
			return False

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
		"""Add app-wide actions."""
		self.add_action_simple('new_window', self.on_new_window_activate)
		self.add_action_simple('settings', self.on_prefs_activate)
		if self.is_beta():
			self.add_action_simple('report_bug', self.on_report_activate)
		self.add_action_simple('shortcuts', self.on_shortcuts_activate)
		self.add_action_simple('help', self.on_help_activate)
		self.add_action_simple('about', self.on_about_activate)
		self.add_action_simple('quit', self.on_quit)

	def add_accels(self):
		"""Set all keyboard shortcuts."""
		self.set_accels_for_action('app.new_window', ['<Ctrl>n'])
		self.set_accels_for_action('app.help', ['F1'])
		self.set_accels_for_action('app.quit', ['<Ctrl>q'])

		self.set_accels_for_action('win.main_color', ['<Ctrl>l'])
		self.set_accels_for_action('win.secondary_color', ['<Ctrl>r'])
		self.set_accels_for_action('win.exchange_color', ['<Ctrl>e'])

		self.set_accels_for_action('win.go_up', ['<Ctrl>Up'])
		self.set_accels_for_action('win.go_down', ['<Ctrl>Down'])
		self.set_accels_for_action('win.go_left', ['<Ctrl>Left'])
		self.set_accels_for_action('win.go_right', ['<Ctrl>Right'])

		self.set_accels_for_action('win.import', ['<Ctrl>i'])
		self.set_accels_for_action('win.paste', ['<Ctrl>v'])
		self.set_accels_for_action('win.select_all', ['<Ctrl>a'])
		self.set_accels_for_action('win.back_to_former_tool', ['<Ctrl>b'])

		self.set_accels_for_action('win.selection_unselect', ['<Ctrl>u'])
		self.set_accels_for_action('win.selection_cut', ['<Ctrl>x'])
		self.set_accels_for_action('win.selection_copy', ['<Ctrl>c'])
		self.set_accels_for_action('win.selection_delete', ['Delete'])

		self.set_accels_for_action('win.main_menu', ['F10'])
		self.set_accels_for_action('win.options_menu', ['<Shift>F10'])
		self.set_accels_for_action('win.toggle_preview', ['<Ctrl>m'])

		self.set_accels_for_action('win.new_tab', ['<Ctrl>t'])
		self.set_accels_for_action('win.close_tab', ['<Ctrl>w'])
		self.set_accels_for_action('win.open', ['<Ctrl>o'])
		self.set_accels_for_action('win.save', ['<Ctrl>s'])
		self.set_accels_for_action('win.save_as', ['<Ctrl><Shift>s'])

		self.set_accels_for_action('win.undo', ['<Ctrl>z'])
		self.set_accels_for_action('win.redo', ['<Ctrl><Shift>z'])

########

	def open_window_with_file(self, gfile):
		"""Open a new window with an optional Gio.File as an argument."""
		win = DrawingWindow(application=self)
		win.present()
		win.init_window_content(gfile) # this optimization has no effect because
		# of GLib unknown magic, but should be kept anyway because the window is
		# presented to the user, making any issue in `init_window_content` very
		# explicit, and likely to be reported.
		return win

	def on_activate(self, *args):
		"""I don't know if this is ever called from the 'activate' signal, but
		it's called by on_cli anyway."""
		win = self.props.active_window
		if not win:
			self.on_new_window_activate()
		else:
			win.present()

	def on_cli(self, *args):
		"""Main handler, managing options and CLI arguments."""
		# This is the list of files given by the command line. If there is none,
		# this will be ['/app/bin/drawing'] which has a length of 1.
		arguments = args[1].get_arguments()

		# Possible options are 'version', 'new-window', and 'new-tab', in this
		# order: only one option can be applied, '-ntv' will be the same as '-v'.
		options = args[1].get_options_dict()

		if options.contains('version'):
			print(_("Drawing") + ' ' + self.version)
			self.on_about_activate()

		# If no file given as argument
		elif options.contains('new-window') and len(arguments) == 1:
			self.on_new_window_activate()
		elif options.contains('new-tab') and len(arguments) == 1:
			win = self.props.active_window
			if not win:
				self.on_new_window_activate()
			else:
				win.present()
				self.props.active_window.build_new_tab(None)
		elif len(arguments) == 1:
			self.on_activate()

		elif options.contains('new-window'):
			self.on_new_window_activate()
			for path in arguments:
				f = self.get_valid_file(args[1], path)
				if f is not None:
					self.open_window_with_file(f)
		else: # giving files without '-n' is equivalent to giving files with '-t'
			for path in arguments:
				f = self.get_valid_file(args[1], path)
				if f is not None:
					win = self.props.active_window
					if not win:
						self.open_window_with_file(f)
					else:
						win.present()
						self.props.active_window.build_new_tab(f)
		# I don't even know if i should return something
		return 0

	def get_valid_file(self, app, path):
		try:
			f = app.create_file_for_arg(path)
			if 'image/' in f.query_info('standard::*', \
				          Gio.FileQueryInfoFlags.NONE, None).get_content_type():
				return f
			else:
				return None
		except:
			# Obviously, do not translate the command line.
			err = _("""Error opening this file. Did you mean
flatpak run --file-forwarding {0} @@ {1} @@
?""")
			print(err.format(APP_ID, path))
			return None

########

	def on_new_window_activate(self, *args):
		"""Action callback, opening a new window with an empty canvas."""
		return self.open_window_with_file(None)

	def on_report_activate(self, *args):
		"""Action callback, opening a new issue on the github repo."""
		win = self.props.active_window
		Gtk.show_uri_on_window(win, self.git_url + '/issues/new', Gdk.CURRENT_TIME)

	def on_shortcuts_activate(self, *args):
		"""Action callback, showing the "shortcuts" dialog."""
		if self.shortcuts_window is not None:
			self.shortcuts_window.destroy()
		builder = Gtk.Builder().new_from_resource( \
		                        '/com/github/maoschanz/Drawing/ui/shortcuts.ui')
		self.shortcuts_window = builder.get_object('shortcuts')
		self.shortcuts_window.present()

	def on_prefs_activate(self, *args):
		"""Action callback, showing the preferences window."""
		if self.prefs_window is not None:
			self.prefs_window.destroy()
		wants_csd = not 'ssd' in self.props.active_window.decorations
		self.prefs_window = DrawingPrefsWindow(self.is_beta(), wants_csd)
		self.prefs_window.present()

	def on_help_activate(self, *args):
		"""Action callback, showing the user help."""
		win = self.props.active_window
		Gtk.show_uri_on_window(win, 'help:drawing', Gdk.CURRENT_TIME)

	def on_about_activate(self, *args):
		"""Action callback, showing the "about" dialog."""
		if self.about_dialog is not None:
			self.about_dialog.destroy()
		self.about_dialog = Gtk.AboutDialog.new()
		self.about_dialog.set_copyright('© 2019 Romain F. T.')
		self.about_dialog.set_authors(['Romain F. T.'])
		# To tranlators: "translate" this by your name, it will be displayed in the "about" dialog
		self.about_dialog.set_translator_credits(_("translator-credits"))
		self.about_dialog.set_artists(['Dmitry Z.'])
		self.about_dialog.set_comments(_("A drawing application for the GNOME desktop."))
		self.about_dialog.set_license_type(Gtk.License.GPL_3_0)
		self.about_dialog.set_logo_icon_name(APP_ID)
		self.about_dialog.set_version(str(self.version))
		self.about_dialog.set_website(self.git_url)
		self.about_dialog.set_website_label(_("Report bugs or ideas"))
		self.about_dialog.run()

	def on_quit(self, *args):
		"""Action callback, quitting the app."""
		self.quit()

