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

import sys, gi, time
from urllib.parse import unquote

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GLib, Gdk

from .window import DrawingWindow
from .preferences import DrawingPrefsWindow

APP_ID = 'com.github.maoschanz.drawing'
APP_PATH = '/com/github/maoschanz/drawing/'

def main(version):
	app = Application(version)
	return app.run(sys.argv)

################################################################################

class Application(Gtk.Application):
	shortcuts_window = None
	prefs_window = None

	# INITIALIZATION ###########################################################

	def __init__(self, version):
		super().__init__(application_id=APP_ID,
		                 flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)

		GLib.set_application_name('Drawing') # XXX drawing ?
		GLib.set_prgname(APP_ID)
		self.version = version
		self.has_tools_in_menubar = False

		self.connect('startup', self.on_startup)
		self.register(None)
		self.connect('activate', self.on_activate)
		self.connect('command-line', self.on_cli)

		self.add_main_option('version', b'v', GLib.OptionFlags.NONE,
		             GLib.OptionArg.NONE, _("Print the version and exit"), None)
		self.add_main_option('new-window', b'n', GLib.OptionFlags.NONE,
		                     GLib.OptionArg.NONE, _("Open a new window"), None)
		self.add_main_option('new-tab', b't', GLib.OptionFlags.NONE,
		                     GLib.OptionArg.NONE, _("Open a new tab"), None)
		self.add_main_option('edit-clipboard', b'c', GLib.OptionFlags.NONE,
		             GLib.OptionArg.NONE, _("Edit the clipboard content"), None)
		self.add_main_option('screenshot', b's', GLib.OptionFlags.NONE,
		          GLib.OptionArg.NONE, _("Take a screenshot and edit it"), None)

		icon_theme = Gtk.IconTheme.get_default()
		icon_theme.add_resource_path(APP_PATH + 'icons')
		icon_theme.add_resource_path(APP_PATH + 'tools/icons')

	def on_startup(self, *args):
		"""Called only once, add app-wide menus and actions, and all accels."""
		self.build_actions()
		builder = Gtk.Builder.new_from_resource(APP_PATH + 'ui/app-menus.ui')
		menubar_model = builder.get_object('menu-bar')
		self.set_menubar(menubar_model)
		if self.prefers_app_menu():
			appmenu_model = builder.get_object('app-menu')
			self.set_app_menu(appmenu_model)

	def build_actions(self):
		"""Add app-wide actions."""
		self.add_action_simple('new_window', self.on_new_window, ['<Ctrl>n'])
		self.add_action_simple('settings', self.on_prefs, None)
		if not self.is_beta():
			self.add_action_simple('report_bug', self.on_report, None)
		self.add_action_simple('shortcuts', self.on_shortcuts, \
		                                         ['<Ctrl>question', '<Ctrl>F1'])
		self.add_action_simple('help', self.on_help_index, ['F1'])
		self.add_action_simple('help_main', self.on_help_main, None)
		self.add_action_simple('help_tools', self.on_help_tools, None)
		self.add_action_simple('help_canvas', self.on_help_canvas, None)
		self.add_action_simple('help_selection', self.on_help_selection, None)
		self.add_action_simple('about', self.on_about, ['<Shift>F1'])
		self.add_action_simple('quit', self.on_quit, ['<Ctrl>q'])

	# WINDOWS AND CLI MANAGEMENT ###############################################

	def open_window_with_content(self, gfile, get_cb):
		"""Open a new window with an optional Gio.File as an argument. If get_cb
		is true, the Gio.File is ignored and the picture is built from the
		clipboard content."""
		win = DrawingWindow(application=self)
		win.present()
		win.init_window_content(gfile, get_cb) # this optimization has no effect
		# because of GLib unknown magic, but should be kept anyway because the
		# window is presented to the user regarless of loading errors, making
		# any issue in `init_window_content` very explicit, and more likely to
		# be reported.
		return win

	def on_activate(self, *args):
		"""I don't know if this is ever called from the 'activate' signal, but
		it's called by on_cli anyway."""
		win = self.props.active_window
		if not win:
			self.on_new_window()
		else:
			win.present()

	def on_cli(self, *args):
		"""Main handler, managing options and CLI arguments."""
		# This is the list of files given by the command line. If there is none,
		# this will be ['/app/bin/drawing'] which has a length of 1.
		arguments = args[1].get_arguments()

		# XXX the following comment is wrong.
		# Possible options are 'version', 'new-window', and 'new-tab', in this
		# order: only one option can be applied, '-ntv' will be the same as '-v'.
		options = args[1].get_options_dict()

		if options.contains('version'):
			print(_("Drawing") + ' ' + self.version)
		elif options.contains('edit-clipboard'):
			self._edit_clipboard(options.contains('new-window'))
		elif options.contains('screenshot'):
			self._edit_screenshot(args[1])

		# If no file given as argument
		elif len(arguments) == 1:
			if options.contains('new-window'):
				self.on_new_window()
			elif options.contains('new-tab'):
				self._new_empty_tab()
			else:
				self.on_activate()

		elif options.contains('new-window'):
			self.on_new_window()
			for fpath in arguments:
				f = self.get_valid_file(args[1], fpath)
				if f is not None:
					self.open_window_with_content(f, False) # XXX dépend si on
					# fait -n ou -nt selon moi, et de toutes manières là on en
					# ouvre trop car il y en a une au début de l'embranchement
		else: # giving files without '-n' is equivalent to giving files with '-t'
			for fpath in arguments:
				f = self.get_valid_file(args[1], fpath)
				if f is not None:
					self._new_tab_with_file(f)
		# I don't even know if i should return something
		return 0

	def _edit_clipboard(self, in_new_window):
		win = self.props.active_window
		if not win or in_new_window:
			self.open_window_with_content(None, True)
		else:
			win.present()
			win.build_image_from_clipboard()

	def _new_empty_tab(self):
		win = self.props.active_window
		if not win:
			self.on_new_window()
		else:
			win.present()
			win.build_new_image()

	def _new_tab_with_file(self, f):
		win = self.props.active_window
		if not win:
			self.open_window_with_content(f, False)
		else:
			win.present()
			self.props.active_window.build_new_tab(gfile=f)

	# SCREENSHOTTING ###########################################################

	# XXX shouldn't it be an action?
	def _edit_screenshot(self, app):
		win = self.props.active_window
		if not win:
			self.on_new_window()
			# Because the portal requires the app to have a window
			# XXX la cacher peut-être ?
		self.cli_app = app
		time.sleep(1) # TODO paramétrable XXX si utile

		bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
		proxy = Gio.DBusProxy.new_sync(bus, Gio.DBusProxyFlags.NONE, None,
				                         'org.freedesktop.portal.Desktop',
				                      '/org/freedesktop/portal/desktop',
				                'org.freedesktop.portal.Screenshot', None)

		args = GLib.Variant('(sa{sv})', ('', {}))
		res = proxy.call_sync('Screenshot', args, \
		                             Gio.DBusCallFlags.NO_AUTO_START, 500, None)
		response_id = bus.signal_subscribe('org.freedesktop.portal.Desktop', \
		           'org.freedesktop.portal.Request', 'Response', res[0], None, \
		       Gio.DBusSignalFlags.NO_MATCH_RULE, self.receive_screenshot, None)

	def receive_screenshot(self, *args):
		useful_data = args[5] # TODO dans toute cette merde ya bien un truc
		# mieux que l'URL ?
		if useful_data[0] == 1:
			# Action cancelled by the user
			return
		win = self.props.active_window
		if not win:
			# Should never happen
			win = self.on_new_window()
		else:
			win.present()
		if useful_data[0] == 0:
			weird_uri = useful_data[1]['uri']
			file_name = weird_uri.split('/')[-1] # XXX honteux
			image_dir = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PICTURES)
			true_uri = 'file://' + image_dir + '/' + file_name # XXX honteux
			fpath = unquote(true_uri) # XXX honteux
			f = self.get_valid_file(self.cli_app, fpath)
			if f is not None:
				self._new_tab_with_file(f)
		elif useful_data[0] == 2:
			win.prompt_message(True, _("Screenshot failed"))

	# ACTIONS CALLBACKS ########################################################

	def on_new_window(self, *args):
		"""Action callback, opening a new window with an empty canvas."""
		return self.open_window_with_content(None, False)

	def on_report(self, *args):
		"""Action callback, opening a new issue on the github repo."""
		win = self.props.active_window
		url = 'https://github.com/maoschanz/drawing/issues/new'
		Gtk.show_uri_on_window(win, url, Gdk.CURRENT_TIME)

	def on_shortcuts(self, *args):
		"""Action callback, showing the 'shortcuts' dialog."""
		if self.shortcuts_window is not None:
			self.shortcuts_window.destroy()
		builder = Gtk.Builder().new_from_resource(APP_PATH + 'ui/shortcuts.ui')
		self.shortcuts_window = builder.get_object('shortcuts')
		self.shortcuts_window.present()

	def on_prefs(self, *args):
		"""Action callback, showing the preferences window."""
		if self.prefs_window is not None:
			self.prefs_window.destroy()
		wants_csd = not 'ssd' in self.props.active_window.decorations
		self.prefs_window = DrawingPrefsWindow(self.is_beta(), wants_csd)
		self.prefs_window.present()

	def on_help_index(self, *args):
		"""Action callback, showing the index of user help manual."""
		self.show_help_page('')

	def on_help_main(self, *args):
		"""Action callback, showing the 'basic features' page of the user help
		manual."""
		self.show_help_page('/main_features')

	def on_help_tools(self, *args):
		"""Action callback, showing the 'classic tools' page of the user help
		manual."""
		self.show_help_page('/tools_classic')

	def on_help_canvas(self, *args):
		"""Action callback, showing the 'canvas and selection tools' page of the
		user help manual."""
		self.show_help_page('/tools_canvas')

	def on_help_selection(self, *args):
		"""Action callback, showing the 'selection' page of the user
		help manual."""
		self.show_help_page('/tools_selection')

	def show_help_page(self, suffix):
		win = self.props.active_window
		Gtk.show_uri_on_window(win, 'help:drawing' + suffix, Gdk.CURRENT_TIME)

	def on_about(self, *args):
		"""Action callback, showing the "about" dialog."""
		about_dialog = Gtk.AboutDialog(transient_for=self.props.active_window,
			copyright='© 2019 Romain F. T.', authors=['Romain F. T.'],
			# To tranlators: "translate" this by your name, it will be displayed
			# in the "about" dialog
			translator_credits=_("translator-credits"),
			artists=['Tobias Bernard', 'Romain F. T.'],
			comments=_("A drawing application for the GNOME desktop."),
			license_type=Gtk.License.GPL_3_0,
			logo_icon_name=APP_ID, version=str(self.version),
			website='https://maoschanz.github.io/drawing/',
			website_label=_("Official webpage"))
		about_dialog.run()
		about_dialog.destroy()

	def on_quit(self, *args):
		"""Action callback, quitting the app."""
		self.quit()

	# UTILITIES ################################################################

	def is_beta(self):
		"""Tells is the app version is even or odd, odd versions being considered
		as unstable versions. This affects available options and the style of
		the headerbar."""
		version_array = self.version.split('.')
		if (int(version_array[1]) * 5) % 10 == 5:
			return True
		else:
			return False

	def add_action_simple(self, action_name, callback, shortcuts):
		action = Gio.SimpleAction.new(action_name, None)
		action.connect('activate', callback)
		self.add_action(action)
		if shortcuts is not None:
			self.set_accels_for_action('app.' + action_name, shortcuts)

	def add_action_boolean(self, action_name, default, callback):
		action = Gio.SimpleAction().new_stateful(action_name, None, \
		                                      GLib.Variant.new_boolean(default))
		action.connect('change-state', callback)
		self.add_action(action)

	def get_valid_file(self, app, path):
		try:
			f = app.create_file_for_arg(path)
			if 'image/' in f.query_info('standard::*', \
				          Gio.FileQueryInfoFlags.NONE, None).get_content_type():
				return f
			else:
				return None # mainly when it's /app/bin/drawing
		except:
			err = _("Error opening this file. Did you mean %s ?")
			command = "\n\tflatpak run --file-forwarding {0} @@ {1} @@\n"
			command = command.format(APP_ID, path)
			print(err % command)
			return None

	############################################################################
################################################################################

