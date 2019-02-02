# window.py
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

from gi.repository import Gtk, Gdk, Gio, GdkPixbuf, GLib
import cairo, os

from .gi_composites import GtkTemplate

from .tool_pencil import ToolPencil
from .tool_select import ToolSelect
from .tool_line import ToolLine
from .tool_paint import ToolPaint
from .tool_text import ToolText
from .tool_picker import ToolPicker
from .tool_shape import ToolShape
from .tool_experiment import ToolExperiment
from .tool_replace import ToolReplace
from .tool_polygon import ToolPolygon
from .tool_crop import ToolCrop
from .tool_scale import ToolScale
from .tool_rotate import ToolRotate

from .image import DrawingImage
from .properties import DrawingPropertiesDialog
from .utilities import utilities_save_pixbuf_at
from .minimap import DrawingMinimap
from .color_popover import DrawingColorPopover

@GtkTemplate(ui='/com/github/maoschanz/Drawing/ui/window.ui')
class DrawingWindow(Gtk.ApplicationWindow):
	__gtype_name__ = 'DrawingWindow'

	_settings = Gio.Settings.new('com.github.maoschanz.Drawing')

	tools_panel = GtkTemplate.Child()
	toolbar_box = GtkTemplate.Child()
	notebook = GtkTemplate.Child()
	bottom_panel_box = GtkTemplate.Child()

	# Default bottom panel
	bottom_panel = GtkTemplate.Child()
	color_box = GtkTemplate.Child()
	color_menu_btn_l = GtkTemplate.Child()
	color_menu_btn_r = GtkTemplate.Child()
	l_btn_image = GtkTemplate.Child()
	r_btn_image = GtkTemplate.Child()
	size_setter = GtkTemplate.Child()
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
		self.init_instance_attributes()
		decorations = self._settings.get_string('decorations')
		self.set_ui_bars(decorations)
		self.build_color_buttons()
		self.minimap = DrawingMinimap(self, self.minimap_btn)
		self.add_all_win_actions()
		self.image_list = []
		self.build_new_image()
		self.init_tools()
		self.update_history_sensitivity()
		self.connect_signals()
		self.set_picture_title()

	def init_instance_attributes(self):
		self.handlers = []
		self.active_tool_id = 'pencil'
		self.former_tool_id = 'pencil'
		self.hijacker_id = None
		self.header_bar = None
		self.main_menu_btn = None
		self.needed_width_for_long = 0

	def init_tools(self):
		"""Initialize all tools, building the UI for them including the menubar,
		and enable the default tool."""
		self.tools = {}
		self.tools['pencil'] = ToolPencil(self)
		self.tools['select'] = ToolSelect(self)
		self.tools['text'] = ToolText(self)
		self.tools['picker'] = ToolPicker(self)
		if self._settings.get_boolean('experimental'):
			self.tools['paint'] = ToolPaint(self)
			self.tools['replace'] = ToolReplace(self)
			self.tools['experiment'] = ToolExperiment(self)
		self.tools['line'] = ToolLine(self)
		self.tools['shape'] = ToolShape(self)
		self.tools['polygon'] = ToolPolygon(self)
		self.tools['crop'] = ToolCrop(self)
		self.tools['scale'] = ToolScale(self)
		self.tools['rotate'] = ToolRotate(self)

		# Side panel
		self.build_tool_rows()

		# Global menubar
		if not self.app.has_tools_in_menubar:
			tools_menu = self.app.get_menubar().get_item_link(4, Gio.MENU_LINK_SUBMENU).get_item_link(0, Gio.MENU_LINK_SECTION)
			for tool_id in self.tools:
				self.tools[tool_id].add_item_to_menu(tools_menu)
			self.app.has_tools_in_menubar = True

		# Initialisation of menus
		self.enable_tool(self.active_tool_id, True)

	def build_new_image(self, *args):
		new_image = DrawingImage(self)
		self.image_list.append(new_image)
		self.notebook.append_page(new_image, new_image.tab_title)
		new_image.init_image()
		self.update_tabs_visibility()
		self.notebook.set_current_page(self.notebook.get_n_pages()-1)

	def close_tab(self, tab):
		# TODO XXX FIXME saving
		index = self.notebook.page_num(tab)
		self.notebook.remove_page(index)
		self.image_list.pop(index)
		self.update_tabs_visibility()

	def update_tabs_visibility(self):
		if self.notebook.get_n_pages() > 1:
			self.notebook.set_show_tabs(True)
		else:
			self.notebook.set_show_tabs(False)

	def action_close(self, *args):
		self.close()

	def on_close(self, *args):
		return not self.confirm_save_modifs()

	# GENERAL PURPOSE METHODS

	def connect_signals(self):
		self.handlers.append( self.connect('delete-event', self.on_close) )
		self.handlers.append( self.connect('configure-event', self.adapt_to_window_size) )
		self.handlers.append( self.options_btn.connect('toggled', self.update_option_label) )
		self.handlers.append( self._settings.connect('changed::panel-width', self.on_show_labels_setting_changed) )

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
		self.add_action_simple('properties', self.action_properties)

		self.add_action_simple('main_menu', self.action_main_menu)
		self.add_action_simple('options_menu', self.action_options_menu)
		self.add_action_simple('toggle_preview', self.action_toggle_preview)

		self.add_action_simple('new_tab', self.build_new_image)
		self.add_action_simple('close', self.action_close)
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
		self.add_action_simple('selection_export', self.action_selection_export)

		self.add_action_simple('back_to_former_tool', self.back_to_former_tool)
		self.add_action_enum('active_tool', 'pencil', self.on_change_active_tool)
		self.add_action_boolean('show_labels', self._settings.get_boolean('panel-width'), \
			self.on_show_labels_changed)

		self.add_action_simple('main_color', self.action_main_color)
		self.add_action_simple('secondary_color', self.action_secondary_color)
		self.add_action_simple('exchange_color', self.action_exchange_color)
		self.app.add_action_boolean('use_editor', \
			self._settings.get_boolean('direct-color-edit'), self.action_use_editor)

		if self._settings.get_boolean('experimental'):
			self.add_action_simple('restore_pixbuf', self.action_restore_pixbuf)
			self.add_action_simple('rebuild_from_histo', self.action_rebuild_from_histo)

	def action_toggle_preview(self, *args):
		self.minimap_btn.set_active(not self.minimap_btn.get_active())

	# XXX
	def action_restore_pixbuf(self, *args):
		self.get_active_image().use_stable_pixbuf()
		self.get_active_image().queue_draw()

	# XXX
	def action_rebuild_from_histo(self, *args):
		self.get_active_image().restore_first_pixbuf()
		h = self.get_active_image().undo_history.copy()
		self.get_active_image().undo_history = []
		for op in h:
			self.tools[op['tool_id']].apply_operation(op)
			print(op)
		self.get_active_image().queue_draw()

	# WINDOW BARS

	def get_edition_status(self):
		return self.active_tool().get_edition_status()

	def set_picture_title(self):
		fn = self.get_file_path()
		if fn is None:
			fn = _("Unsaved file")
		main_title = fn.split('/')[-1]
		if not self.get_active_image()._is_saved:
			main_title = '*' + main_title
		subtitle = self.get_edition_status()
		self.set_title(_("Drawing") + ' - ' + main_title + ' - ' + subtitle)
		if self.header_bar is not None:
			self.header_bar.set_title(main_title)
			self.header_bar.set_subtitle(subtitle)

	def set_ui_bars(self, decorations):
		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/Drawing/ui/menus.ui')
		self.placeholder_model = builder.get_object('tool-placeholder')
		if decorations == 'csd':
			self.build_headerbar()
			self.set_titlebar(self.header_bar)
			self.set_show_menubar(False)
		elif decorations == 'everything':
			self.build_headerbar()
			self.set_titlebar(self.header_bar)
			self.set_show_menubar(True)
			self.build_toolbar()
		elif decorations == 'ssd-menubar':
			self.set_show_menubar(True)
		elif decorations == 'ssd-toolbar':
			self.build_toolbar()
			self.set_show_menubar(False)
		else:
			self.build_toolbar()
			self.set_show_menubar(True)

	def build_toolbar(self):
		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/Drawing/ui/toolbar.ui')
		toolbar = builder.get_object('toolbar')
		self.toolbar_box.add(toolbar)
		self.toolbar_box.show_all()

	def build_headerbar(self):
		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/Drawing/ui/headerbar.ui')
		self.header_bar = builder.get_object('header_bar')
		self.save_label = builder.get_object('save_label')
		self.save_icon = builder.get_object('save_icon')
		self.add_btn = builder.get_object('add_btn')
		self.main_menu_btn = builder.get_object('main_menu_btn')

		builder.add_from_resource('/com/github/maoschanz/Drawing/ui/menus.ui')
		short_main_menu = builder.get_object('short-window-menu')
		self.short_menu_popover = Gtk.Popover.new_from_model(self.main_menu_btn, short_main_menu)
		long_main_menu = builder.get_object('long-window-menu')
		self.long_menu_popover = Gtk.Popover.new_from_model(self.main_menu_btn, long_main_menu)

		add_menu = builder.get_object('add-menu')
		add_popover = Gtk.Popover.new_from_model(self.add_btn, add_menu)
		self.add_btn.set_popover(add_popover)

	def action_main_menu(self, *args):
		if self.main_menu_btn is not None:
			self.main_menu_btn.set_active(not self.main_menu_btn.get_active())

	def action_options_menu(self, *args):
		self.options_btn.set_active(not self.options_btn.get_active())

	def adapt_to_window_size(self, *args):
		if self.header_bar is not None:
			if self.get_allocated_width() > 600:
				self.save_label.set_visible(True)
				self.save_icon.set_visible(False)
				self.add_btn.set_visible(True)
				self.main_menu_btn.set_popover(self.short_menu_popover)
			else:
				self.save_label.set_visible(False)
				self.save_icon.set_visible(True)
				self.add_btn.set_visible(False)
				self.main_menu_btn.set_popover(self.long_menu_popover)

		if self.active_tool().implements_panel:
			self.active_tool().adapt_to_window_size()
		else:
			available_width = self.bottom_panel_box.get_allocated_width()
			if self.minimap_label.get_visible():
				self.needed_width_for_long = self.color_box.get_allocated_width() + \
					self.size_setter.get_allocated_width() + \
					self.options_long_box.get_preferred_width()[0] + \
					self.minimap_label.get_preferred_width()[0]
			if self.needed_width_for_long > 0.7 * available_width:
				self.compact_preview_btn(True)
				self.compact_options_btn(True)
			else:
				self.compact_options_btn(False)
				self.compact_preview_btn(False)

	def compact_options_btn(self, state):
		self.options_short_box.set_visible(state)
		self.options_long_box.set_visible(not state)

	def compact_preview_btn(self, state):
		self.minimap_label.set_visible(not state)
		self.minimap_arrow.set_visible(not state)
		self.minimap_icon.set_visible(state)

	# TOOLS PANEL

	def build_tool_rows(self):
		group = None
		for tool_id in self.tools:
			if group is None:
				group = self.tools[tool_id].row
			else:
				self.tools[tool_id].row.join_group(group)
			self.tools_panel.add(self.tools[tool_id].row)
		self.tools_panel.show_all()
		self.on_show_labels_setting_changed()

	def set_tools_labels_visibility(self, visible):
		if visible:
			self.tools_panel.show_all()
		else:
			for label in self.tools:
				self.tools[label].label_widget.set_visible(False)

	def on_show_labels_setting_changed(self, *args):
		self.set_tools_labels_visibility(self._settings.get_boolean('panel-width'))

	def on_show_labels_changed(self, *args):
		show_labels = not args[0].get_state()
		self._settings.set_boolean('panel-width', show_labels)
		args[0].set_state(GLib.Variant.new_boolean(show_labels))

	# TOOLS

	def on_change_active_tool(self, *args): # FIXME on n'a jamais de panneau custom quand on fait depuis la menubar
		state_as_string = args[1].get_string()
		if state_as_string == args[0].get_state().get_string():
			return
		elif self.tools[state_as_string].row.get_active():
			args[0].set_state(GLib.Variant.new_string(state_as_string))
		else:
			self.tools[state_as_string].row.set_active(True)
		self.enable_tool(state_as_string, True)

	def enable_tool(self, new_tool_id, should_give_back_control):
		former_tool_id_2 = self.former_tool_id
		self.former_tool_id = self.active_tool_id
		if should_give_back_control:
			self.former_tool().give_back_control()
		self.former_tool().on_tool_unselected()
		self.get_active_image().queue_draw()
		self.active_tool_id = new_tool_id
		self.update_bottom_panel()
		self.active_tool().on_tool_selected()
		#self.minimap.correct_coords()
		self.set_picture_title()
		if self.former_tool().implements_panel:
			self.former_tool_id = former_tool_id_2

	def update_bottom_panel(self):
		self.adapt_to_window_size() # XXX redondant ?
		self.build_options_menu()
		self.active_tool().show_panel(True)
		if self.former_tool().implements_panel or self.active_tool().implements_panel:
			self.former_tool().show_panel(False)
		elif not self.active_tool().implements_panel:
			self.update_size_spinbtn_state()
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

	def tool_needs_selection(self):
		return self.active_tool().need_selection_pixbuf

	# FILE MANAGEMENT

	def action_properties(self, *args):
		self.get_active_image().edit_properties()

	def get_active_image(self):
		return self.image_list[self.notebook.get_current_page()]

	def get_file_path(self):
		return self.get_active_image().get_file_path()

	def action_open(self, *args):
		gfile = self.file_chooser_open()
		if gfile is None:
			return
		if not self.get_active_image()._is_saved:
			dialog = Gtk.MessageDialog(modal=True, title=_("Unsaved modifications"), \
				transient_for=self)
			dialog.add_button(_("New tab"), Gtk.ResponseType.OK)
			dialog.add_button(_("New window"), Gtk.ResponseType.ACCEPT)
			dialog.add_button(_("Here (discard changes)"), Gtk.ResponseType.APPLY)
			dialog.get_message_area().add(Gtk.Label( \
				label=( _("There are unsaved modifications to %s.") % \
				self.get_active_image().get_filename_for_display() ) ))
			dialog.get_message_area().add(Gtk.Label( \
				label=(_("Where do you want to open %s?")%(gfile.get_path().split('/')[-1])) ))
			dialog.show_all()
			result = dialog.run()
			if result == Gtk.ResponseType.OK:
				self.build_new_image()
			elif result == Gtk.ResponseType.ACCEPT:
				self.app.open_window_with_file(gfile)
				dialog.destroy()
				return
			dialog.destroy()
		self.try_load_file(gfile)

	def file_chooser_open(self, *args):
		gfile = None
		file_chooser = Gtk.FileChooserNative.new(_("Open a picture"), self,
			Gtk.FileChooserAction.OPEN,
			_("Open"),
			_("Cancel"))
		allPictures = Gtk.FileFilter()
		allPictures.set_name(_("All pictures"))
		allPictures.add_mime_type('image/png')
		allPictures.add_mime_type('image/jpeg')
		allPictures.add_mime_type('image/bmp')
		file_chooser.add_filter(allPictures)
		response = file_chooser.run()
		if response == Gtk.ResponseType.ACCEPT:
			gfile = file_chooser.get_file()
		file_chooser.destroy()
		return gfile

	def action_save(self, *args):
		fn = self.get_file_path()
		if fn is None:
			gfile = self.file_chooser_save('')
			if gfile is not None:
				self.get_active_image().gfile = gfile
		fn = self.get_file_path()
		if fn is not None:
			utilities_save_pixbuf_at(self.get_active_image().main_pixbuf, fn)
		self.get_active_image().post_save()
		self.set_picture_title()

	def action_save_as(self, *args):
		gfile = self.file_chooser_save('')
		if gfile is not None:
			self.get_active_image().gfile = gfile
		self.action_save()

	def try_load_file(self, gfile):
		if gfile is not None:
			self.get_active_image().try_load_file(gfile)

	def confirm_save_modifs(self):
		if not self.get_active_image()._is_saved:
			fn = self.get_file_path()
			if fn is None:
				unsaved_file_name = _("Untitled") + '.png'
			else:
				unsaved_file_name = fn.split('/')[-1]
			dialog = Gtk.MessageDialog(modal=True, title=_("Unsaved modifications"), \
				transient_for=self)
			dialog.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
			dialog.add_button(_("Discard"), Gtk.ResponseType.NO)
			dialog.add_button(_("Save"), Gtk.ResponseType.APPLY)
			dialog.get_message_area().add(Gtk.Label(
				label=( _("There are unsaved modifications to %s.") % \
				self.get_active_image().get_filename_for_display() ) ))
			dialog.show_all()
			result = dialog.run()
			if result == Gtk.ResponseType.APPLY:
				dialog.destroy()
				self.action_save()
				return True
			elif result == Gtk.ResponseType.NO:
				dialog.destroy()
				return True
			else:
				dialog.destroy()
				return False
		else:
			return True

	def file_chooser_save(self, file_type):
		gfile = None
		file_chooser = Gtk.FileChooserNative.new(_("Save picture as…"), self,
			Gtk.FileChooserAction.SAVE,
			_("Save"),
			_("Cancel"))

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

		if file_type == 'png': # XXX still useful ??
			file_chooser.add_filter(pngPictures)
			file_chooser.add_filter(allPictures)
		elif file_type == 'jpeg':
			file_chooser.add_filter(jpegPictures)
			file_chooser.add_filter(allPictures)
		elif file_type == 'bmp':
			file_chooser.add_filter(bmpPictures)
			file_chooser.add_filter(allPictures)
		else:
			file_chooser.add_filter(allPictures)
			file_chooser.add_filter(pngPictures)
			file_chooser.add_filter(jpegPictures)
			file_chooser.add_filter(bmpPictures)
			file_type = 'png'

		default_file_name = str(_("Untitled") + '.' + file_type)
		file_chooser.set_current_name(default_file_name)

		response = file_chooser.run()
		if response == Gtk.ResponseType.ACCEPT:
			gfile = file_chooser.get_file()
		file_chooser.destroy()
		return gfile

	def action_export_as(self, *args):
		gfile = self.file_chooser_save('')
		if gfile is not None:
			utilities_save_pixbuf_at(self.main_pixbuf, gfile.get_path())

	def action_print(self, *args):
		self.get_active_image().print_image()

	def action_select_all(self, *args):
		self.force_selection_tool()
		self.get_active_image().image_select_all()
		self.get_selection_tool().selection_select_all()

	def action_paste(self, *args):
		self.force_selection_tool()
		self.get_selection_tool().selection_paste()

	def action_import(self, *args):
		file_chooser = Gtk.FileChooserNative.new(_("Import a picture"), self,
			Gtk.FileChooserAction.OPEN,
			_("Import"),
			_("Cancel"))
		allPictures = Gtk.FileFilter()
		allPictures.set_name(_("All pictures"))
		allPictures.add_mime_type('image/png')
		allPictures.add_mime_type('image/jpeg')
		allPictures.add_mime_type('image/bmp')
		file_chooser.add_filter(allPictures)
		response = file_chooser.run()
		if response == Gtk.ResponseType.ACCEPT:
			self.force_selection_tool()
			fn = file_chooser.get_filename()
			self.get_active_image().set_selection_pixbuf(GdkPixbuf.Pixbuf.new_from_file(fn))
			self.get_selection_tool().selection_import()
		file_chooser.destroy()

	def action_selection_export(self, *args):
		gfile = self.file_chooser_save('')
		if gfile is not None:
			utilities_save_pixbuf_at(self.get_active_image().get_selection_pixbuf(), gfile.get_path())

	def get_selection_tool(self):
		return self.tools['select']

	def force_selection_tool(self):
		self.get_selection_tool().row.set_active(True)

	# HISTORY MANAGEMENT

	def action_undo(self, *args):
		self.get_active_image().try_undo()

	def action_redo(self, *args):
		self.get_active_image().try_redo()

	def update_history_sensitivity(self): #XXX
		self.get_active_image().update_history_sensitivity()

	# COLORS

	def build_color_buttons(self):
		white = Gdk.RGBA(red=1.0, green=1.0, blue=1.0, alpha=1.0)
		black = Gdk.RGBA(red=0.0, green=0.0, blue=0.0, alpha=1.0)
		#black = Gdk.RGBA(red=0.8, green=0.5, blue=0.3, alpha=0.8) # TODO as settings
		self.color_popover_r = DrawingColorPopover(self.color_menu_btn_r, self.r_btn_image, white)
		self.color_popover_l = DrawingColorPopover(self.color_menu_btn_l, self.l_btn_image, black)

	def action_use_editor(self, *args):
		self._settings.set_boolean('direct-color-edit', not args[0].get_state())
		args[0].set_state(GLib.Variant.new_boolean(not args[0].get_state()))
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

	def update_size_spinbtn_state(self):
		self.size_setter.set_sensitive(self.active_tool().use_size)

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

