# main.py
#
# Copyright 2018-2022 Romain F. T.
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

import sys, gi, datetime
gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Gtk, Gio, GLib, Gdk
from .window import DrWindow
from .preferences import DrPrefsWindow
from .utilities_files import utilities_gfile_is_image

def main(version):
	app = Application(version)
	return app.run(sys.argv)

################################################################################

class Application(Gtk.Application):
	shortcuts_window = None
	prefs_window = None

	APP_ID = 'com.github.maoschanz.drawing'
	APP_PATH = '/com/github/maoschanz/drawing'
	BUG_REPORT_URL = 'https://github.com/maoschanz/drawing/issues/new/choose'
	FLATPAK_BINARY_PATH = '/app/bin/drawing'
	CURRENT_BINARY_PATH = ''

	############################################################################
	# Initialization ###########################################################

	def __init__(self, version):
		super().__init__(application_id=self.APP_ID,
		                 flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)

		GLib.set_application_name(_("Drawing"))
		GLib.set_prgname(self.APP_ID)
		self._version = version
		self.has_tools_in_menubar = False
		self.runs_in_sandbox = False

		self.connect('startup', self.on_startup)
		self.register(None)
		self.connect('activate', self.on_activate)
		self.connect('command-line', self.on_cli)

		self.add_main_option('version', b'v', GLib.OptionFlags.NONE,
		                     # Description of a command line option
		                     GLib.OptionArg.NONE, _("Show the app version"), None)
		self.add_main_option('new-window', b'n', GLib.OptionFlags.NONE,
		                     # Description of a command line option
		                     GLib.OptionArg.NONE, _("Open a new window"), None)
		self.add_main_option('new-tab', b't', GLib.OptionFlags.NONE,
		                     # Description of a command line option
		                     GLib.OptionArg.NONE, _("Open a new tab"), None)
		self.add_main_option('edit-clipboard', b'c', GLib.OptionFlags.NONE,
		             # Description of a command line option
		             GLib.OptionArg.NONE, _("Edit the clipboard content"), None)

		icon_theme = Gtk.IconTheme.get_default()
		icon_theme.add_resource_path(self.APP_PATH + '/icons')
		icon_theme.add_resource_path(self.APP_PATH + '/tools/icons')

	def on_startup(self, *args):
		"""Called only once, add app-wide menus and actions, and all accels."""
		self._build_actions()
		builder = Gtk.Builder.new_from_resource(self.APP_PATH + '/ui/app-menus.ui')
		menubar_model = builder.get_object('menu-bar')
		self.set_menubar(menubar_model)

	def _build_actions(self):
		"""Add all app-wide actions."""
		self.add_action_simple('new_window', self.on_new_window, ['<Ctrl>n'])
		self.add_action_simple('settings', self.on_prefs)

		current_date = datetime.datetime.now()
		if current_date.month == 4 and current_date.day == 1:
			self.add_action_simple('april-fools', self.on_april_fools)

		self.add_action_simple('help', self.on_help_index, ['F1'])
		self.add_action_simple('help_main', self.on_help_main)
		self.add_action_simple('help_zoom', self.on_help_zoom)
		self.add_action_simple('help_fullscreen', self.on_help_fullscreen)
		self.add_action_simple('help_tools', self.on_help_tools)
		self.add_action_simple('help_colors', self.on_help_colors)
		self.add_action_simple('help_transform', self.on_help_transform)
		self.add_action_simple('help_selection', self.on_help_selection)
		self.add_action_simple('help_prefs', self.on_help_prefs)
		self.add_action_simple('help_whats_new', self.on_help_whats_new)

		self.add_action_simple('report-issue', self.on_report)
		self.add_action_simple('shortcuts', self.on_shortcuts, \
		                                         ['<Ctrl>question', '<Ctrl>F1'])
		self.add_action_simple('about', self.on_about, ['<Shift>F1'])
		self.add_action_simple('quit', self.on_quit, ['<Ctrl>q'])

	############################################################################
	# Opening windows & CLI handling ###########################################

	def open_window_with_content(self, gfile, get_cb, check_duplicates=True):
		"""Open a new window with an optional Gio.File as an argument. If get_cb
		is true, the Gio.File is ignored and the picture is built from the
		clipboard content."""
		if gfile is not None and check_duplicates:
			w, already_opened_index = self.has_image_opened(gfile.get_path())
			if w is not None:
				if not w.confirm_open_twice(gfile):
					w.notebook.set_current_page(already_opened_index)
					return

		win = DrWindow(application=self)
		win.present()

		content_params = {'gfile': gfile, 'get_cb': get_cb}
		# Parameters are: time in milliseconds, method, data # XXX todo?
		# GLib.timeout_add(10, win.init_window_content_async, content_params)
		win.init_window_content_async(content_params)
		return win

	def on_activate(self, *args):
		"""I don't know if this is ever called from the 'activate' signal, but
		it's called anyways."""
		win = self.props.active_window
		if not win:
			self.on_new_window()
		else:
			win.present()

	def on_cli(self, gio_app, gio_command_line):
		"""Main handler, managing options and CLI arguments.
		Arguments are a `Gio.Application` and a `Gio.ApplicationCommandLine`."""

		# This is the list of files given by the command line. If there is none,
		# this will be ['/app/bin/drawing'] which has a length of 1.
		arguments = gio_command_line.get_arguments()
		self.CURRENT_BINARY_PATH = arguments[0]
		if self.CURRENT_BINARY_PATH == self.FLATPAK_BINARY_PATH:
			self.runs_in_sandbox = True

		# Possible options are 'version', 'edit-clipboard', 'new-tab', and
		# 'new-window', in this order: only one option can be applied, '-ntvc'
		# will be understood as '-v'.
		options = gio_command_line.get_options_dict()

		if options.contains('version'):
			print(_("Drawing") + ' ' + self._version)
			if self.is_beta():
				print(_("This version isn't stable!"))
			print()
			print(_("Report bugs or ideas") + " 👉️ " + self.BUG_REPORT_URL)

		elif options.contains('edit-clipboard'):
			win = self.props.active_window
			if not win:
				self.open_window_with_content(None, True)
			else:
				win.present()
				win.build_image_from_clipboard()

		elif options.contains('new-tab') and len(arguments) == 1:
			# If '-t' but no file given as argument
			win = self.props.active_window
			if not win:
				self.on_new_window()
			else:
				win.present()
				win.build_blank_image()

		elif options.contains('new-window'):
			# it opens one new window per file given as argument, or just one
			# new window if no argument is a valid enough file.
			windows_counter = 0
			for fpath in arguments[1:]:
				f = self._get_valid_file(gio_command_line, fpath)
				# here, f can be a GioFile or a boolean. True would mean the app
				# should open a new blank image.
				if f == False:
					continue
				f = None if f == True else f
				self.open_window_with_content(f, False)
				windows_counter = windows_counter + 1
			if windows_counter == 0:
				self.on_new_window()

		elif len(arguments) == 1:
			self.on_activate()

		else:
			# giving files without '-n' is equivalent to giving files with '-t'
			for fpath in arguments[1:]:
				f = self._get_valid_file(gio_command_line, fpath)
				# here f can be a Gio.File or a boolean: True would mean the app
				# should open a new blank image.
				if f == False:
					continue
				win = self.props.active_window
				if not win:
					f = None if f == True else f
					self.open_window_with_content(f, False)
				else:
					win.present()
					if f == True:
						win.build_blank_image()
					else:
						win.build_new_from_file(gfile=f)

		# I don't even know if i should return something
		return 0

	############################################################################
	# Actions callbacks ########################################################

	def on_new_window(self, *args):
		"""Action callback, opening a new window with an empty canvas."""
		return self.open_window_with_content(None, False)

	def on_report(self, *args):
		"""Action callback, opening a new issue on the github repo."""
		win = self.props.active_window
		Gtk.show_uri_on_window(win, self.BUG_REPORT_URL, Gdk.CURRENT_TIME)

	def on_shortcuts(self, *args):
		"""Action callback, showing the 'shortcuts' dialog."""
		if self.shortcuts_window is not None:
			self.shortcuts_window.destroy()
		builder = Gtk.Builder().new_from_resource(self.APP_PATH + '/ui/shortcuts.ui')
		self.shortcuts_window = builder.get_object('shortcuts-window')
		self.shortcuts_window.present()

	def on_prefs(self, *args):
		"""Action callback, showing the preferences window."""
		if self.prefs_window is not None:
			self.prefs_window.destroy()
		wants_csd = 'h' in self.props.active_window.deco_layout
		self.prefs_window = DrPrefsWindow(self.is_beta(), wants_csd, \
		                                                       application=self)
		self.prefs_window.present()

	def on_april_fools(self, *args):
		"""Action callback, rickrolling the user."""
		Gtk.show_uri_on_window(
			self.props.active_window, \
			'https://www.youtube.com/watch?v=dQw4w9WgXcQ',\
			Gdk.CURRENT_TIME \
		)

	def on_help_index(self, *args):
		"""Action callback, showing the index of user help manual."""
		self._show_help_page('')

	def on_help_main(self, *args):
		self._show_help_page('/main_features')

	def on_help_zoom(self, *args):
		self._show_help_page('/zoom_preview')

	def on_help_fullscreen(self, *args):
		self._show_help_page('/fullscreen')

	def on_help_tools(self, *args):
		self._show_help_page('/tools_classic')

	def on_help_colors(self, *args):
		self._show_help_page('/tools_classic_colors')

	def on_help_transform(self, *args):
		self._show_help_page('/tools_transform')

	def on_help_selection(self, *args):
		self._show_help_page('/tools_selection')

	def on_help_prefs(self, *args):
		self._show_help_page('/preferences')

	def on_help_whats_new(self, *args):
		self._show_help_page('/whats_new')

	def on_about(self, *args):
		"""Action callback, showing the "about" dialog."""
		about_dialog = Gtk.AboutDialog(transient_for=self.props.active_window,
			copyright="© 2018-2022 Romain F. T.",
			authors=["Romain F. T.", "Fábio Colacio", "Alexis Lozano"],
			# To tranlators: "translate" this by a list of your names (one name
			# per line), they will be displayed in the "about" dialog
			translator_credits=_("translator-credits"),
			artists=["Tobias Bernard", "Romain F. T.",
			# To translators: this is credits for the icons, consider that "Art
			# Libre" is proper name
			                       _("GNOME's \"Art Libre\" icon set authors")],
			comments=_("Simple image editor for Linux"),
			license_type=Gtk.License.GPL_3_0,
			logo_icon_name=self.APP_ID, version=str(self._version),
			website='https://maoschanz.github.io/drawing/',
			website_label=_("Official webpage"))
		bug_report_btn = Gtk.LinkButton(halign=Gtk.Align.CENTER, visible=True, \
		               label=_("Report bugs or ideas"), uri=self.BUG_REPORT_URL)
		# about_dialog.get_content_area().add(bug_report_btn) # should i?
		about_dialog.set_icon_name('com.github.maoschanz.drawing')

		about_dialog.run()
		about_dialog.destroy()

	def on_quit(self, *args):
		"""Action callback, quitting the entire app."""
		if self.shortcuts_window is not None:
			self.shortcuts_window.destroy()
		if self.prefs_window is not None:
			self.prefs_window.destroy()

		can_quit = True
		# Try (= ask confirmation) to quit the main window(s)
		main_windows = self.get_windows()
		for w in main_windows:
			if w.on_close():
				# User clicked on "cancel"
				can_quit = False
			else:
				w.close()
				w.destroy()

		# The expected behavior, but now theoretically useless, since closing all
		# appwindows should quit automatically. It's too violent to be left
		# without a guard clause.
		if can_quit:
			self.quit()

	############################################################################
	# Utilities ################################################################

	def is_beta(self):
		"""Tells is the app version is even or odd, odd versions being considered
		as unstable versions. This affects available options and the style of
		the headerbar."""
		return (int(self._version.split('.')[1]) * 5) % 10 == 5

	def get_current_version(self):
		return self._version

	def add_action_simple(self, action_name, callback, shortcuts=[]):
		action = Gio.SimpleAction.new(action_name, None)
		action.connect('activate', callback)
		self.add_action(action)
		self.set_accels_for_action('app.' + action_name, shortcuts)

	def add_action_boolean(self, action_name, default, callback):
		action = Gio.SimpleAction().new_stateful(action_name, None, \
		                                      GLib.Variant.new_boolean(default))
		action.connect('change-state', callback)
		self.add_action(action)

	def _show_help_page(self, suffix):
		win = self.props.active_window
		Gtk.show_uri_on_window(win, 'help:drawing' + suffix, Gdk.CURRENT_TIME)

	def has_image_opened(self, file_path):
		"""Returns the window in which the given file is opened, and the index
		of the tab where it is in the window's notebook.
		Or `None, None` otherwise."""
		for win in self.get_windows():
			position_in_window = win.has_image_opened(file_path)
			if position_in_window is not None:
				return win, position_in_window
		return None, None

	def _get_valid_file(self, app, path):
		"""Creates a GioFile object if the path corresponds to an image. If no
		GioFile can be created, it returns a boolean telling whether or not a
		window should be opened anyway."""
		if path == self.CURRENT_BINARY_PATH:
			# when it's CURRENT_BINARY_PATH, the situation is normal (no error)
			# and nothing to open.
			return False

		err = _("Error opening this file.") + ' '
		try:
			gfile = app.create_file_for_arg(path)
		except Exception as excp:
			if self.runs_in_sandbox:
				command = "\n\tflatpak run --file-forwarding {0} @@ {1} @@\n"
				command = command.format(self.APP_ID, path)
				# This is an error message, %s is a better command suggestion
				err = err + _("Did you mean %s ?") % command
			else:
				err = err + excp.message
			print(err) # TODO show that message in an empty window
			return False

		is_image, err = utilities_gfile_is_image(gfile, err)
		if is_image:
			return gfile
		else:
			print(err) # TODO show that message in an empty window
			return True

	############################################################################
################################################################################

