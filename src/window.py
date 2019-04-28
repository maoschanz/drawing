# window.py
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

import os

from gi.repository import Gtk, Gdk, Gio, GdkPixbuf, GLib
from .gi_composites import GtkTemplate

from .tool_addalpha import ToolAddAlpha
from .tool_arc import ToolArc
from .tool_circle import ToolCircle
from .tool_crop import ToolCrop
from .tool_experiment import ToolExperiment
from .tool_flip import ToolFlip
from .tool_freeshape import ToolFreeshape
from .tool_line import ToolLine
from .tool_paint import ToolPaint
from .tool_pencil import ToolPencil
from .tool_picker import ToolPicker
from .tool_polygon import ToolPolygon
from .tool_rectangle import ToolRectangle
from .tool_rotate import ToolRotate
from .tool_saturate import ToolSaturate
from .tool_scale import ToolScale
from .tool_select import ToolSelect
from .tool_text import ToolText

from .image import DrawingImage
from .properties import DrawingPropertiesDialog
from .utilities import utilities_save_pixbuf_at
from .minimap import DrawingMinimap
from .options_manager import DrawingOptionsManager
from .color_popover import DrawingColorPopover
from .message_dialog import DrawingMessageDialog
from .headerbar import DrawingAdaptativeHeaderBar

UI_PATH = '/com/github/maoschanz/drawing/ui/'

@GtkTemplate(ui=UI_PATH+'window.ui')
class DrawingWindow(Gtk.ApplicationWindow):
	__gtype_name__ = 'DrawingWindow'

	_settings = Gio.Settings.new('com.github.maoschanz.drawing')

	# Window empty widgets
	tools_panel = GtkTemplate.Child()
	toolbar_box = GtkTemplate.Child()
	info_bar = GtkTemplate.Child()
	info_label = GtkTemplate.Child()
	notebook = GtkTemplate.Child()
	bottom_panel_box = GtkTemplate.Child()

	# Default bottom panel
	bottom_panel = GtkTemplate.Child()
	color_box = GtkTemplate.Child()
	color_menu_btn_l = GtkTemplate.Child()
	color_menu_btn_r = GtkTemplate.Child()
	l_btn_image = GtkTemplate.Child()
	r_btn_image = GtkTemplate.Child()
	thickness_spinbtn = GtkTemplate.Child()
	options_btn = GtkTemplate.Child()
	options_label = GtkTemplate.Child()
	options_long_box = GtkTemplate.Child()
	options_short_box = GtkTemplate.Child()
	minimap_btn = GtkTemplate.Child()
	minimap_icon = GtkTemplate.Child()
	minimap_label = GtkTemplate.Child()
	minimap_arrow = GtkTemplate.Child()

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.app = kwargs['application']
		self.init_template()

		self.header_bar = None
		self.main_menu_btn = None
		self.has_good_limits = False

		if self._settings.get_boolean('maximized'):
			self.maximize()
		self.set_ui_bars()

	def init_window_content(self, gfile):
		"""Initialize the window's content, such as the minimap, the color
		popovers, the tools, their options, and a new default image."""
		self.hijacker_id = None
		self.tools = None
		self.minimap = DrawingMinimap(self, self.minimap_btn)
		self.options_manager = DrawingOptionsManager(self)
		self.thickness_spinbtn.set_value(self._settings.get_int('last-size'))
		self.limit_size_bottom = 600
		self.limit_size_header = 700

		self.build_color_buttons()
		self.add_all_win_actions()
		self.build_new_tab(gfile)
		self.init_tools()
		self.connect_signals()
		self.set_picture_title()
		self.prompt_message(False, 'window successfully started')

	def set_cursor(self, is_custom):
		if is_custom:
			name = self.active_tool().cursor_name
		else:
			name = 'default'
		cursor = Gdk.Cursor.new_from_name(Gdk.Display.get_default(), name)
		self.get_window().set_cursor(cursor)

	def init_tools(self):
		"""Initialize all tools, building the UI for them including the menubar,
		and enable the default tool."""
		self.tools = {}
		self.tools['pencil'] = ToolPencil(self)
		self.tools['select'] = ToolSelect(self)
		self.tools['text'] = ToolText(self)
		self.tools['picker'] = ToolPicker(self)
		self.tools['addalpha'] = ToolAddAlpha(self)
		self.tools['paint'] = ToolPaint(self)
		self.tools['line'] = ToolLine(self)
		self.tools['arc'] = ToolArc(self)
		self.tools['rectangle'] = ToolRectangle(self)
		self.tools['circle'] = ToolCircle(self)
		self.tools['polygon'] = ToolPolygon(self)
		self.tools['freeshape'] = ToolFreeshape(self)
		if self._settings.get_boolean('devel-only'):
			self.tools['experiment'] = ToolExperiment(self)
		self.tools['crop'] = ToolCrop(self)
		self.tools['scale'] = ToolScale(self)
		self.tools['rotate'] = ToolRotate(self)
		self.tools['flip'] = ToolFlip(self)
		self.tools['saturate'] = ToolSaturate(self)

		# Buttons for tools (in the side panel and the selection tool action bar)
		self.build_tool_rows()

		# Global menubar
		if not self.app.has_tools_in_menubar:
			drawing_tools_section = self.app.get_menubar().get_item_link(4, \
				Gio.MENU_LINK_SUBMENU).get_item_link(0, Gio.MENU_LINK_SECTION)
			canvas_tools_section = self.app.get_menubar().get_item_link(4, \
				Gio.MENU_LINK_SUBMENU).get_item_link(1, Gio.MENU_LINK_SECTION).get_item_link(0, \
				Gio.MENU_LINK_SUBMENU).get_item_link(0, Gio.MENU_LINK_SECTION)
			for tool_id in self.tools:
				if self.tools[tool_id].is_hidden:
					self.tools[tool_id].add_item_to_menu(canvas_tools_section)
				else:
					self.tools[tool_id].add_item_to_menu(drawing_tools_section)
			self.app.has_tools_in_menubar = True

		# Initialisation of options and menus
		tool_id = self._settings.get_string('last-active-tool')
		if tool_id not in self.tools:
			tool_id = 'pencil'
		self.active_tool_id = tool_id
		self.former_tool_id = tool_id
		if tool_id == 'pencil':
			self.enable_tool(tool_id, True)
		else:
			self.active_tool().row.set_active(True)

	def build_new_image(self, *args):
		"""Open a new tab with a drawable blank image."""
		self.build_new_tab(None)
		self.set_picture_title()

	def build_new_tab(self, gfile):
		"""Open a new tab with an optional file to open in it."""
		new_image = DrawingImage(self)
		self.notebook.append_page(new_image, new_image.tab_title)
		if gfile is None:
			new_image.init_background()
		else:
			new_image.try_load_file(gfile)
		self.update_tabs_visibility()
		self.notebook.set_current_page(self.notebook.get_n_pages()-1)

	def on_active_tab_changed(self, *args):
		self.change_active_tool_for(self.active_tool_id)
		# On pourrait être moins bourrin et conserver la sélection, mais flemme
		self.set_picture_title(args[1].update_title())

	def close_tab(self, tab):
		"""Close a tab (after asking to save if needed)."""
		index = self.notebook.page_num(tab)
		if not self.notebook.get_nth_page(index)._is_saved:
			self.notebook.set_current_page(index)
			is_saved = self.confirm_save_modifs()
			if not is_saved:
				return False
		self.notebook.remove_page(index)
		self.update_tabs_visibility()
		return True

	def action_close_tab(self, *args):
		if self.notebook.get_n_pages() > 1:
			self.get_active_image().try_close_tab()
		else:
			self.close()

	def action_close_window(self, *args):
		self.close()

	def on_close(self, *args):
		"""Event callback when trying to close a window. It saves/closes each
		tab and saves the current window settings in order to restore them."""
		while self.notebook.get_n_pages() != 0:
			if not self.get_active_image().try_close_tab():
				return True

		self._settings.set_int('last-size', int(self.thickness_spinbtn.get_value()))
		self._settings.set_string('last-active-tool', self.active_tool_id)
		rgba = self.color_popover_l.color_widget.get_rgba()
		rgba = [str(rgba.red), str(rgba.green), str(rgba.blue), str(rgba.alpha)]
		self._settings.set_strv('last-left-rgba', rgba)
		rgba = self.color_popover_r.color_widget.get_rgba()
		rgba = [str(rgba.red), str(rgba.green), str(rgba.blue), str(rgba.alpha)]
		self._settings.set_strv('last-right-rgba', rgba)

		self._settings.set_boolean('maximized', self.is_maximized())
		return False

	# GENERAL PURPOSE METHODS

	def connect_signals(self):
		self.info_bar.connect('close', self.hide_message)
		self.info_bar.connect('response', self.hide_message)
		self.connect('delete-event', self.on_close)
		self.connect('configure-event', self.adapt_to_window_size)
		self.options_btn.connect('toggled', self.update_option_label)
		self._settings.connect('changed::show-labels', self.on_show_labels_setting_changed)
		self._settings.connect('changed::decorations', self.on_layout_changed)
		self.notebook.connect('switch-page', self.on_active_tab_changed)

	def add_action_simple(self, action_name, callback):
		"""Convenient wrapper method adding a stateless action to the window. It
		will be named 'action_name' (string) and activating the action will
		trigger the method 'callback'."""
		action = Gio.SimpleAction.new(action_name, None)
		action.connect("activate", callback)
		self.add_action(action)

	def add_action_boolean(self, action_name, default, callback):
		"""Convenient wrapper method adding a stateful action to the window. It
		will be named 'action_name' (string), be created with the state 'default'
		(boolean), and activating the action will trigger the method 'callback'."""
		action = Gio.SimpleAction().new_stateful(action_name, None, \
			GLib.Variant.new_boolean(default))
		action.connect('change-state', callback)
		self.add_action(action)

	def add_action_enum(self, action_name, default, callback):
		"""Convenient wrapper method adding a stateful action to the window. It
		will be named 'action_name' (string), be created with the state 'default'
		(string), and changing the active target of the action will trigger the
		method 'callback'."""
		action = Gio.SimpleAction().new_stateful(action_name, \
			GLib.VariantType.new('s'), GLib.Variant.new_string(default))
		action.connect('change-state', callback)
		self.add_action(action)

	def add_all_win_actions(self):
		"""This doesn't add all window-wide GioActions, but only the GioActions
		which are here "by default", independently of any tool."""

		self.add_action_simple('main_menu', self.action_main_menu)
		self.add_action_simple('options_menu', self.action_options_menu)
		self.add_action_boolean('toggle_preview', False, self.action_toggle_preview)
		self.add_action_simple('properties', self.action_properties)
		self.add_action_boolean('show_labels', self._settings.get_boolean('show-labels'), \
			self.on_show_labels_changed)

		self.add_action_simple('go_up', self.action_go_up)
		self.add_action_simple('go_down', self.action_go_down)
		self.add_action_simple('go_left', self.action_go_left)
		self.add_action_simple('go_right', self.action_go_right)

		self.add_action_simple('new_tab', self.build_new_image)
		self.add_action_simple('close_tab', self.action_close_tab)
		self.add_action_simple('close', self.action_close_window)
		self.add_action_simple('save', self.action_save)
		self.add_action_simple('open', self.action_open)
		self.add_action_simple('undo', self.action_undo)
		self.add_action_simple('redo', self.action_redo)
		self.add_action_simple('save_as', self.action_save_as)
		self.add_action_simple('export_as', self.action_export_as)
		self.add_action_simple('print', self.action_print)
		self.add_action_simple('import', self.action_import)
		self.add_action_simple('paste', self.action_paste)
		self.add_action_simple('select_all', self.action_select_all)

		# Is declared here because its callback need several methods from this
		# file but none from select.py
		self.add_action_simple('selection_export', self.action_selection_export)

		self.add_action_simple('back_to_former_tool', self.back_to_former_tool)
		self.add_action_simple('force_selection_tool', self.force_selection_tool)
		self.add_action_enum('active_tool', 'pencil', self.on_change_active_tool)
		self.add_action_simple('apply_selection_tool', self.action_apply_selection_tool)

		self.add_action_simple('main_color', self.action_main_color)
		self.add_action_simple('secondary_color', self.action_secondary_color)
		self.add_action_simple('exchange_color', self.action_exchange_color)

		self.app.add_action_boolean('use_editor', \
			self._settings.get_boolean('direct-color-edit'), self.action_use_editor)

		if self._settings.get_boolean('devel-only'):
			self.add_action_simple('restore_pixbuf', self.action_restore_pixbuf)
			self.add_action_simple('rebuild_from_histo', self.action_rebuild_from_histo)

	# WINDOW BARS

	def on_layout_changed(self, *args):
		self.prompt_message(True, _("Modifications will take effect in the next new window."))

	def get_edition_status(self):
		return self.active_tool().get_edition_status()

	def set_picture_title(self, *args):
		"""Set the window's title and subtitle (regardless of the preferred UI
		bars), and the active tab title. Tools have to be initilized before
		calling this method, because they provide the subtitle."""
		if len(args) == 1:
			main_title = args[0]
		else:
			main_title = self.get_active_image().update_title()
		subtitle = self.get_edition_status()

		self.set_title(_("Drawing") + ' - ' + main_title + ' - ' + subtitle)
		if self.header_bar is not None:
			self.header_bar.header_bar.set_title(main_title)
			self.header_bar.header_bar.set_subtitle(subtitle)

	def get_auto_decorations(self):
		"""Return the decorations setting based on the XDG_CURRENT_DESKTOP
		environment variable."""
		desktop_env = os.getenv('XDG_CURRENT_DESKTOP', 'GNOME')
		if 'GNOME' in desktop_env:
			return 'csd'
		elif 'Pantheon' in desktop_env:
			return 'csd-eos'
		elif 'Unity' in desktop_env:
			return 'ssd-toolbar'
		elif 'Cinnamon' in desktop_env or 'MATE' in desktop_env or 'XFCE' in desktop_env:
			return 'ssd'
		else:
			return 'csd' # Use the GNOME layout if the desktop is unknown,
		# because i don't know how the env variable is on mobile.
		# Since hipsterwm users love "ricing", they'll be happy to edit
		# preferences themselves if they hate CSD.

	def set_ui_bars(self):
		"""Set the UI "bars" (headerbar, menubar, title, toolbar, whatever)
		according to the user's preference, which by default is 'auto'."""
		# Loading a whole file in a GtkBuilder just for this looked ridiculous,
		# so it's built from a string.
		builder = Gtk.Builder.new_from_string('''
<?xml version="1.0"?>
<interface>
  <menu id="tool-placeholder">
    <section>
      <item>
        <attribute name="action">none</attribute>
        <attribute name="label">''' + _("No options") + '''</attribute>
      </item>
    </section>
  </menu>
</interface>''', -1)
		self.placeholder_model = builder.get_object('tool-placeholder')

		# Remember the setting, so no need to restart this at each dialog.
		self.decorations = self._settings.get_string('decorations')
		if self.decorations == 'auto':
			self.decorations = self.get_auto_decorations()

		if self.decorations == 'csd':
			self.build_headerbar(False)
			self.set_titlebar(self.header_bar.header_bar)
			self.set_show_menubar(False)
		elif self.decorations == 'csd-eos':
			self.build_headerbar(True)
			self.set_titlebar(self.header_bar.header_bar)
			self.set_show_menubar(False)
		elif self.decorations == 'everything': # devel-only
			self.build_headerbar(False)
			self.set_titlebar(self.header_bar.header_bar)
			self.set_show_menubar(True)
			self.build_toolbar()
		elif self.decorations == 'ssd-menubar':
			self.set_show_menubar(True)
		elif self.decorations == 'ssd-toolbar':
			self.build_toolbar()
			self.set_show_menubar(False)
		else: # self.decorations == 'ssd'
			self.build_toolbar()
			self.set_show_menubar(True)

		if self.app.is_beta():
			self.get_style_context().add_class('devel')

	def build_toolbar(self):
		builder = Gtk.Builder.new_from_resource(UI_PATH+'toolbar.ui')
		toolbar = builder.get_object('toolbar')
		self.toolbar_box.add(toolbar)
		self.toolbar_box.show_all()

	def build_headerbar(self, is_eos):
		"""Build the window's headerbar. If "is_eos" is true, the headerbar will
		follow elementaryOS guidelines, else it will follow GNOME guidelines."""
		self.header_bar = DrawingAdaptativeHeaderBar(is_eos)

	def action_main_menu(self, *args):
		if self.main_menu_btn is not None:
			self.main_menu_btn.set_active(not self.main_menu_btn.get_active())

	def action_options_menu(self, *args):
		"""This displays/hides the tool's options menu, and is implemented as an
		action to ease the accelerator (shift+f10). This action could be
		disable when the current panel doesn't contain the corresponding button,
		but will not be."""
		self.options_btn.set_active(not self.options_btn.get_active())

	def set_bottom_width_limit(self): # XXX devrait se transmettre aux panneaux custom
		if not self.has_good_limits: # heureusement ils marchent assez bien tous seuls
			return
		self.bottom_panel.show_all()
		self.limit_size_bottom = self.color_box.get_preferred_width()[0] + \
			self.thickness_spinbtn.get_preferred_width()[0] + \
			self.options_long_box.get_preferred_width()[0] + \
			self.minimap_label.get_preferred_width()[0]
		self.bottom_panel.set_visible(not self.active_tool().implements_panel)

	def init_adaptability(self):
		"""Initialize limit_size_header and limit_size_bottom, which are 700 by
		default, but are likely to actually be less wide."""
		self.has_good_limits = True

		# Bottom panel width limit
		self.set_bottom_width_limit()

		# Header bar width limit
		if self.header_bar is not None:
			self.header_bar.init_adaptability()

	def adapt_to_window_size(self, *args):
		"""Adapts the headerbar (if any) and the default bottom panel to the new
		window size. If the current bottom panel isn't the default one, this will
		call the tool method applying the new size to the tool panel."""
		if not self.has_good_limits and self.get_allocated_width() > 700:
			self.init_adaptability()

		if self.header_bar is not None:
			self.header_bar.adapt_to_window_size()

		available_width = self.bottom_panel_box.get_allocated_width()
		# print(available_width)
		for tool_id in self.tools:
			self.tools[tool_id].adapt_to_window_size(available_width)
		if not self.active_tool().implements_panel:
			if self.limit_size_bottom > 0.7 * available_width:
				self.compact_bottombar(True)
			else:
				self.compact_bottombar(False)

	def compact_headerbar(self, state):
		self.save_label.set_visible(not state)
		self.save_icon.set_visible(state)
		self.add_btn.set_visible(not state)

	def compact_bottombar(self, state):
		self.options_short_box.set_visible(state)
		self.options_long_box.set_visible(not state)
		self.minimap_label.set_visible(not state)
		self.minimap_arrow.set_visible(not state)
		self.minimap_icon.set_visible(state)

	def hide_message(self, *args):
		self.prompt_message(False, '')

	def prompt_message(self, show, label):
		"""Update the content and the visibility of the info bar."""
		self.info_bar.set_visible(show)
		if show:
			self.info_label.set_label(label)
		if self._settings.get_boolean('devel-only'):
			print('Drawing: ' + label)

	def update_tabs_visibility(self):
		self.notebook.set_show_tabs(self.notebook.get_n_pages() > 1)

	# TOOLS PANEL

	def build_tool_rows(self):
		"""Adds each tool's button to the side panel, or to the selection's
		bottom panel."""
		group = None
		for tool_id in self.tools:
			if group is None:
				group = self.tools[tool_id].row
			else:
				self.tools[tool_id].row.join_group(group)
			self.tools_panel.add(self.tools[tool_id].row)
			if self.tools[tool_id].is_hidden:
				self.get_selection_tool().add_subtool(self.tools[tool_id])
		self.on_show_labels_setting_changed()

	def set_tools_labels_visibility(self, visible):
		if visible:
			for tool_id in self.tools:
				self.tools[tool_id].label_widget.set_visible(True)
		else:
			for tool_id in self.tools:
				self.tools[tool_id].label_widget.set_visible(False)

	def on_show_labels_setting_changed(self, *args):
		# TODO https://lazka.github.io/pgi-docs/Gio-2.0/classes/Settings.html#Gio.Settings.create_action
		self.set_tools_labels_visibility(self._settings.get_boolean('show-labels'))

	def on_show_labels_changed(self, *args):
		show_labels = not args[0].get_state()
		self._settings.set_boolean('show-labels', show_labels)
		args[0].set_state(GLib.Variant.new_boolean(show_labels))

	# TOOLS

	def on_change_active_tool(self, *args):
		state_as_string = args[1].get_string()
		if state_as_string == args[0].get_state().get_string():
			return
		else:
			self.change_active_tool_for(state_as_string)

	def change_active_tool_for(self, tool_id):
		action = self.lookup_action('active_tool')
		if self.tools[tool_id].row.get_active():
			action.set_state(GLib.Variant.new_string(tool_id))
			self.enable_tool(tool_id, True)
		else:
			self.tools[tool_id].row.set_active(True)

	def enable_tool(self, new_tool_id, should_give_back_control):
		self.former_tool_id = self.active_tool_id
		if should_give_back_control:
			self.former_tool().give_back_control()
		self.former_tool().on_tool_unselected()
		self.get_active_image().queue_draw()
		self.active_tool_id = new_tool_id
		self.update_bottom_panel()
		self.active_tool().on_tool_selected()
		self.set_picture_title()

	def update_bottom_panel(self):
		"""Show the correct bottom panel, with the correct tool options menu."""
		self.build_options_menu()
		if self.former_tool_id is not self.active_tool_id:
			self.former_tool().show_panel(False)
		self.active_tool().show_panel(True)
		self.set_bottom_width_limit()
		self.update_thickness_spinbtn_state()
		self.adapt_to_window_size()

	def active_tool(self):
		return self.tools[self.active_tool_id]

	def former_tool(self):
		return self.tools[self.former_tool_id]

	def back_to_former_tool(self, *args):
		if self.hijacker_id is not None:
			self.hijack_end()
		else:
			self.tools[self.former_tool_id].row.set_active(True)

	def hijack_begin(self, hijacker_id, target_id):
		self.lookup_action('active_tool').set_enabled(False)
		self.hijacker_id = hijacker_id
		self.enable_tool(target_id, False)

	def hijack_end(self):
		if self.hijacker_id is not None:
			self.enable_tool(self.hijacker_id, False)
		self.hijacker_id = None
		self.lookup_action('active_tool').set_enabled(True)

	# FILE MANAGEMENT

	def action_properties(self, *args):
		DrawingPropertiesDialog(self, self.get_active_image())

	def get_active_image(self):
		return self.notebook.get_nth_page(self.notebook.get_current_page())

	def get_file_path(self):
		return self.get_active_image().get_file_path()

	def action_open(self, *args):
		gfile = self.file_chooser_open()
		if gfile is None:
			return
		else:
			self.prompt_message(True, _("Loading %s") % \
				(gfile.get_path().split('/')[-1]))
		if self.get_active_image()._is_saved:
			self.try_load_file(gfile)
		else:
			dialog = DrawingMessageDialog(self)
			dialog.set_actions([_("New Tab"), _("New Window"), _("Discard changes")])
			dialog.add_string( _("There are unsaved modifications to %s.") % \
				self.get_active_image().get_filename_for_display() )
			dialog.add_string( _("Where do you want to open %s?") %  \
				(gfile.get_path().split('/')[-1]) )
			result = dialog.run()
			dialog.destroy()
			if result == 1:
				self.build_new_tab(gfile)
			elif result == 3:
				self.try_load_file(gfile)
			elif result == 2:
				self.app.open_window_with_file(gfile)
		self.hide_message()

	def file_chooser_open(self, *args):
		"""Opens an "open" file chooser dialog, and return a GioFile or None."""
		gfile = None
		file_chooser = Gtk.FileChooserNative.new(_("Open a picture"), self,
			Gtk.FileChooserAction.OPEN,
			_("Open"),
			_("Cancel"))
		self.add_filechooser_filters(file_chooser)

		response = file_chooser.run()
		if response == Gtk.ResponseType.ACCEPT:
			gfile = file_chooser.get_file()
		file_chooser.destroy()
		return gfile

	def action_save(self, *args):
		fn = self.get_file_path()
		if fn is None:
			gfile = self.file_chooser_save()
			if gfile is not None:
				self.get_active_image().gfile = gfile
		fn = self.get_file_path()
		if fn is not None:
			utilities_save_pixbuf_at(self.get_active_image().main_pixbuf, fn)
			self.get_active_image().post_save()
		self.set_picture_title()

	def action_save_as(self, *args):
		gfile = self.file_chooser_save()
		if gfile is not None:
			self.get_active_image().gfile = gfile
			self.action_save()

	def try_load_file(self, gfile):
		if gfile is not None:
			self.get_active_image().try_load_file(gfile)
		self.set_picture_title() # often redundant but not useless
		self.prompt_message(False, 'file successfully loaded')

	def confirm_save_modifs(self):
		"""Return True if the image can be closed/overwritten (whether it's saved
		or not), or False if the image can't be closed/overwritten."""
		if self.get_active_image()._is_saved:
			return True
		fn = self.get_file_path()
		if fn is None:
			unsaved_file_name = _("Untitled") + '.png'
			display_name = _("this picture")
		else:
			unsaved_file_name = fn.split('/')[-1]
			display_name = self.get_active_image().get_filename_for_display()
		dialog = DrawingMessageDialog(self)
		dialog.set_actions([_("Cancel"), _("Discard"), _("Save")])
		dialog.add_string( _("There are unsaved modifications to %s.") % display_name)
		self.minimap.update_minimap()
		image = Gtk.Image().new_from_pixbuf(self.minimap.mini_pixbuf)
		frame = Gtk.Frame(valign=Gtk.Align.CENTER, halign=Gtk.Align.CENTER)
		frame.add(image)
		dialog.add_widget(frame)
		result = dialog.run()
		dialog.destroy()
		if result == 3: # Save
			self.action_save()
			return True
		elif result == 2: # Discard
			return True
		else: # Cancel
			return False

	def add_filechooser_filters(self, dialog):
		"""Add file filters for images to file chooser dialogs."""
		allPictures = Gtk.FileFilter()
		allPictures.set_name(_("All pictures"))
		allPictures.add_mime_type('image/png')
		allPictures.add_mime_type('image/jpeg')
		allPictures.add_mime_type('image/bmp')

		pngPictures = Gtk.FileFilter()
		pngPictures.set_name(_("PNG images"))
		pngPictures.add_mime_type('image/png')

		jpegPictures = Gtk.FileFilter()
		jpegPictures.set_name(_("JPEG images"))
		jpegPictures.add_mime_type('image/jpeg')

		bmpPictures = Gtk.FileFilter()
		bmpPictures.set_name(_("BMP images"))
		bmpPictures.add_mime_type('image/bmp')

		dialog.add_filter(allPictures)
		dialog.add_filter(pngPictures)
		dialog.add_filter(jpegPictures)
		dialog.add_filter(bmpPictures)

	def file_chooser_save(self):
		"""Opens an "save" file chooser dialog, and return a GioFile or None."""
		gfile = None
		file_chooser = Gtk.FileChooserNative.new(_("Save picture as…"), self,
			Gtk.FileChooserAction.SAVE,
			_("Save"),
			_("Cancel"))
		self.add_filechooser_filters(file_chooser)
		default_file_name = str(_("Untitled") + '.png')
		file_chooser.set_current_name(default_file_name)

		response = file_chooser.run()
		if response == Gtk.ResponseType.ACCEPT:
			gfile = file_chooser.get_file()
		file_chooser.destroy()
		return gfile

	def action_export_as(self, *args):
		gfile = self.file_chooser_save()
		if gfile is not None:
			utilities_save_pixbuf_at(self.get_active_image().main_pixbuf, gfile.get_path())

	def action_print(self, *args):
		self.get_active_image().print_image()

	def action_select_all(self, *args):
		self.force_selection_tool()
		self.get_active_image().image_select_all()
		self.get_selection_tool().selection_select_all()

	def action_paste(self, *args):
		cb = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
		pixbuf = cb.wait_for_image()
		if pixbuf is not None:
			self.force_selection_tool()
			self.get_active_image().set_selection_pixbuf(pixbuf)
			self.get_selection_tool().selection_paste()
		else:
			string =  cb.wait_for_text()
			self.tools['text'].row.set_active(True)
			self.active_tool().set_string(string)
			self.active_tool().on_release_on_area(None, None, None, 100, 100)

	def action_import(self, *args):
		file_chooser = Gtk.FileChooserNative.new(_("Import a picture"), self,
			Gtk.FileChooserAction.OPEN,
			_("Import"),
			_("Cancel"))
		self.add_filechooser_filters(file_chooser)
		response = file_chooser.run()
		if response == Gtk.ResponseType.ACCEPT:
			self.force_selection_tool()
			fn = file_chooser.get_filename()
			self.get_active_image().set_selection_pixbuf( \
			                                 GdkPixbuf.Pixbuf.new_from_file(fn))
			self.get_selection_tool().selection_import()
		file_chooser.destroy()

	def action_selection_export(self, *args):
		gfile = self.file_chooser_save()
		if gfile is not None:
			utilities_save_pixbuf_at( \
			   self.get_active_image().get_selection_pixbuf(), gfile.get_path())

	def get_selection_tool(self):
		return self.tools['select']

	def force_selection_tool(self, *args):
		if self.hijacker_id is not None:
			self.hijack_end()
		else:
			self.get_selection_tool().row.set_active(True)

	def action_apply_selection_tool(self, *args):
		self.active_tool().on_apply_temp_pixbuf_tool_operation()

	def tool_needs_selection(self):
		return ( self.active_tool() is self.get_selection_tool() )

	# HISTORY MANAGEMENT

	def action_undo(self, *args):
		self.get_active_image().try_undo()
		self.action_rebuild_from_histo()

	def action_redo(self, *args):
		self.get_active_image().try_redo()
		self.action_rebuild_from_histo()

	def operation_is_ongoing(self): # TODO
		# if self.active_tool() is self.get_selection_tool():
		# 	is_ongoing = self.active_tool().selection_has_been_used
		# else:
		# 	is_ongoing = self.active_tool().has_ongoing_operation
		# return is_ongoing
		return False

	def action_restore_pixbuf(self, *args):
		self.get_active_image().use_stable_pixbuf()
		self.get_active_image().queue_draw()

	def action_rebuild_from_histo(self, *args):
		self.get_active_image().restore_first_pixbuf()
		h = self.get_active_image().undo_history.copy()
		self.get_active_image().undo_history = []
		for op in h:
			self.tools[op['tool_id']].apply_operation(op)
		self.get_active_image().queue_draw()
		self.get_active_image().update_history_sensitivity(True)

	# COLORS

	def build_color_buttons(self):
		"""Initialize the 2 color buttons and popovers with the 2 previously
		memorized RGBA values."""
		right_rgba = self._settings.get_strv('last-right-rgba')
		r = float(right_rgba[0])
		g = float(right_rgba[1])
		b = float(right_rgba[2])
		a = float(right_rgba[3])
		right_rgba = Gdk.RGBA(red=r, green=g, blue=b, alpha=a)
		left_rgba = self._settings.get_strv('last-left-rgba')
		r = float(left_rgba[0])
		g = float(left_rgba[1])
		b = float(left_rgba[2])
		a = float(left_rgba[3])
		left_rgba = Gdk.RGBA(red=r, green=g, blue=b, alpha=a)
		self.color_popover_r = DrawingColorPopover(self.color_menu_btn_r, \
		                                           self.r_btn_image, right_rgba)
		self.color_popover_l = DrawingColorPopover(self.color_menu_btn_l, \
		                                           self.l_btn_image, left_rgba)

	def action_use_editor(self, *args):
		use_editor = not args[0].get_state()
		self._settings.set_boolean('direct-color-edit', use_editor)
		args[0].set_state(GLib.Variant.new_boolean(use_editor))
		self.set_palette_setting()

	def set_palette_setting(self, *args):
		show_editor = self._settings.get_boolean('direct-color-edit')
		self.color_popover_r.setting_changed(show_editor)
		self.color_popover_l.setting_changed(show_editor)

	def action_main_color(self, *args):
		self.color_menu_btn_l.activate()

	def action_secondary_color(self, *args):
		self.color_menu_btn_r.activate()

	def action_exchange_color(self, *args):
		left_c = self.color_popover_l.color_widget.get_rgba()
		self.color_popover_l.color_widget.set_rgba(self.color_popover_r.color_widget.get_rgba())
		self.color_popover_r.color_widget.set_rgba(left_c)

	# TOOLS OPTIONS

	def update_thickness_spinbtn_state(self):
		self.thickness_spinbtn.set_sensitive(self.active_tool().use_size)

	def build_options_menu(self):
		widget = self.active_tool().get_options_widget()
		model = self.active_tool().get_options_model()
		if model is None:
			self.app.get_menubar().remove(5)
			self.app.get_menubar().insert_submenu(5, _("_Options"), self.placeholder_model)
		else:
			self.app.get_menubar().remove(5)
			self.app.get_menubar().insert_submenu(5, _("_Options"), model)
		if widget is not None:
			self.options_btn.set_popover(widget)
		elif model is not None:
			self.options_btn.set_menu_model(model)
		else:
			self.options_btn.set_popover(None)
		self.update_option_label()

	def update_option_label(self, *args):
		self.options_label.set_label(self.active_tool().get_options_label())

	# PREVIEW & NAVIGATION

	def action_toggle_preview(self, *args):
		"""Action callback, showing or hiding the "minimap" preview popover."""
		preview_visible = not args[0].get_state()
		if preview_visible:
			self.minimap.popup()
			self.minimap.update_minimap()
		else:
			self.minimap.popdown()
		args[0].set_state(GLib.Variant.new_boolean(preview_visible))

	def action_go_up(self, *args):
		self.get_active_image().add_deltas(0, -1, 100)

	def action_go_down(self, *args):
		self.get_active_image().add_deltas(0, 1, 100)

	def action_go_left(self, *args):
		self.get_active_image().add_deltas(-1, 0, 100)

	def action_go_right(self, *args):
		self.get_active_image().add_deltas(1, 0, 100)

