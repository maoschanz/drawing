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

from .properties import DrawingPropertiesDialog
from .utilities import save_pixbuf_at
from .minimap import DrawingMinimap
from .color_popover import DrawingColorPopover

@GtkTemplate(ui='/com/github/maoschanz/Drawing/ui/window.ui')
class DrawingWindow(Gtk.ApplicationWindow):
	__gtype_name__ = 'DrawingWindow'

	_settings = Gio.Settings.new('com.github.maoschanz.Drawing')

	paned_area = GtkTemplate.Child()
	tools_panel = GtkTemplate.Child()
	toolbar_box = GtkTemplate.Child()
	drawing_area = GtkTemplate.Child()
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

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.app = kwargs['application']
		self.init_template()
		self.init_instance_attributes()

		decorations = self._settings.get_string('decorations')
		self.set_ui_bars(decorations)

		self.build_color_buttons()
		self.minimap = DrawingMinimap(self, self.minimap_btn)

		self.drawing_area.add_events( \
			Gdk.EventMask.BUTTON_PRESS_MASK | \
			Gdk.EventMask.BUTTON_RELEASE_MASK | \
			Gdk.EventMask.BUTTON_MOTION_MASK | \
			Gdk.EventMask.SMOOTH_SCROLL_MASK)
		self.add_all_win_actions()

		self.init_tools()

		self.update_history_sensitivity()
		self.connect_signals()

		self.init_background()
		self.set_picture_title()

	def init_instance_attributes(self):
		self.handlers = []
		self.active_tool_id = 'pencil'
		self.former_tool_id = 'pencil'
		self.hijacker_id = None
		self.is_clicked = False
		self.header_bar = None
		self.main_menu_btn = None

		self.undo_history = []
		self.redo_history = []
		self.gfile = None
		self.filename = None
		self._is_saved = True
		self.needed_width_for_long = 0

		width = self._settings.get_int('default-width')
		height = self._settings.get_int('default-height')
		self.main_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, width, height) # 8 ??? les autres plantent
		self.temporary_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 1, 1)
		self.surface = cairo.ImageSurface(cairo.Format.ARGB32, width, height)

	def init_tools(self):
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

	def init_background(self, *args):
		w_context = cairo.Context(self.surface)
		r = float(self._settings.get_strv('default-rgba')[0])
		g = float(self._settings.get_strv('default-rgba')[1])
		b = float(self._settings.get_strv('default-rgba')[2])
		a = float(self._settings.get_strv('default-rgba')[3])
		w_context.set_source_rgba(r, g, b, a)
		w_context.paint()
		self.on_tool_finished()

	def initial_save(self):
		self.set_picture_title()
		self._is_saved = True
		self.use_stable_pixbuf()
		self.drawing_area.queue_draw()

	def action_close(self, *args):
		self.close()

	def on_close(self, *args):
		return not self.confirm_save_modifs()

	# GENERAL PURPOSE METHODS

	def connect_signals(self):
		self.handlers.append( self.connect('delete-event', self.on_close) )
		self.handlers.append( self.connect('configure-event', self.adapt_to_window_size) )

		self.handlers.append( self.drawing_area.connect('draw', self.on_draw) )
		self.handlers.append( self.drawing_area.connect('motion-notify-event', self.on_motion_on_area) )
		self.handlers.append( self.drawing_area.connect('button-press-event', self.on_press_on_area) )
		self.handlers.append( self.drawing_area.connect('button-release-event', self.on_release_on_area) )
		self.handlers.append( self.drawing_area.connect('scroll-event', self.on_scroll_on_area) )

		self.options_btn.connect('toggled', self.update_option_label)

		self.handlers.append( self._settings.connect('changed::panel-width', self.on_show_labels_setting_changed) )

	def add_action_simple(self, action_name, callback):
		action = Gio.SimpleAction.new(action_name, None)
		action.connect("activate", callback)
		self.add_action(action)

	def add_action_boolean(self, action_name, default, callback):
		action = Gio.SimpleAction().new_stateful(action_name, None, \
			GLib.Variant.new_boolean(default))
		action.connect('change-state', callback)
		self.add_action(action)

	def add_action_enum(self, action_name, default, callback):
		action = Gio.SimpleAction().new_stateful(action_name, \
			GLib.VariantType.new('s'), GLib.Variant.new_string(default))
		action.connect('change-state', callback)
		self.add_action(action)

	def add_all_win_actions(self):
		self.add_action_simple('properties', self.edit_properties)

		self.add_action_simple('main_menu', self.action_main_menu)
		self.add_action_simple('options_menu', self.action_options_menu)
		self.add_action_simple('toggle_preview', self.action_toggle_preview)

		self.add_action_simple('close', self.action_close)
		self.add_action_simple('save', self.action_save)
		self.add_action_simple('open', self.action_open)
		self.add_action_simple('undo', self.action_undo)
		self.add_action_simple('redo', self.action_redo)
		self.add_action_simple('save_as', self.action_save_as)
		self.add_action_simple('export_as', self.action_export_as)
		self.add_action_simple('print', self.action_print)

		self.add_action_simple('back_to_former_tool', self.back_to_former_tool)
		self.add_action_enum('active_tool', 'pencil', self.on_change_active_tool)
		self.add_action_boolean('show_labels', self._settings.get_boolean('panel-width'), \
			self.on_show_labels_changed)

		self.add_action_simple('main_color', self.action_main_color)
		self.add_action_simple('secondary_color', self.action_secondary_color)
		self.add_action_simple('exchange_color', self.action_exchange_color)
		self.app.add_action_boolean('use_editor', \
			self._settings.get_boolean('direct-color-edit'), self.action_use_editor)

	def action_toggle_preview(self, *args):
		self.minimap_btn.set_active(not self.minimap_btn.get_active())

	# WINDOW BARS

	def get_edition_status(self):
		return self.active_tool().get_edition_status()

	def set_picture_title(self):
		fn = self.get_file_path()
		if fn is None:
			fn = _("Unsaved file")
		main_title = fn.split('/')[-1]
		if not self._is_saved:
			main_title = '*' + main_title
		subtitle = self.get_edition_status()
		self.set_title(_("Drawing") + ' - ' + main_title + ' - ' + subtitle)
		if self.header_bar is not None:
			self.header_bar.set_title(main_title)
			self.header_bar.set_subtitle(subtitle)

	def set_ui_bars(self, decorations):
		if decorations == 'csd':
			self.build_headerbar()
			self.set_titlebar(self.header_bar)
			self.set_show_menubar(False)
		elif decorations == 'everything':
			self.build_headerbar()
			self.set_titlebar(self.header_bar)
			self.set_show_menubar(True)
			self.build_toolbar()
		elif decorations == 'ssd-toolbar':
			self.set_show_menubar(True)
			self.build_toolbar()
		else:
			self.set_show_menubar(True)

	def build_toolbar(self):
		builder = Gtk.Builder.new_from_resource("/com/github/maoschanz/Drawing/ui/toolbar.ui")
		toolbar = builder.get_object("toolbar")
		self.toolbar_box.add(toolbar)
		self.toolbar_box.show_all()

	def build_headerbar(self):
		builder = Gtk.Builder.new_from_resource("/com/github/maoschanz/Drawing/ui/headerbar.ui")
		self.header_bar = builder.get_object("header_bar")
		self.save_label = builder.get_object("save_label")
		self.save_icon = builder.get_object("save_icon")
		add_btn = builder.get_object("add_btn")
		self.add_label = builder.get_object("add_label")
		self.add_icon = builder.get_object("add_icon")
		self.main_menu_btn = builder.get_object("main_menu_btn")

		builder.add_from_resource("/com/github/maoschanz/Drawing/ui/menus.ui")
		main_menu = builder.get_object("window-menu")
		menu_popover = Gtk.Popover.new_from_model(self.main_menu_btn, main_menu)
		self.main_menu_btn.set_popover(menu_popover)
		add_menu = builder.get_object("add-menu")
		add_popover = Gtk.Popover.new_from_model(add_btn, add_menu)
		add_btn.set_popover(add_popover)

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
				self.add_label.set_visible(True)
				self.add_icon.set_visible(False)
			else:
				self.save_label.set_visible(False)
				self.save_icon.set_visible(True)
				self.add_label.set_visible(False)
				self.add_icon.set_visible(True)

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
			self.paned_area.set_position(self.tools_panel.get_preferred_width()[0])
		else:
			for label in self.tools:
				self.tools[label].label_widget.set_visible(False)
			self.paned_area.set_position(0)

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
		self.drawing_area.queue_draw()
		self.active_tool_id = new_tool_id
		self.update_bottom_panel()
		self.active_tool().on_tool_selected()
		self.minimap.correct_coords()
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

	# FILE MANAGEMENT

	def get_file_path(self):
		if self.gfile is None:
			return None
		else:
			return self.gfile.get_path()

	def action_open(self, *args):
		if self.confirm_save_modifs():
			self.file_chooser_open()
			self.try_load_file()

	def file_chooser_open(self, *args):
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
			self.gfile = file_chooser.get_file()
		file_chooser.destroy()

	def action_save(self, *args):
		fn = self.get_file_path()
		if fn is None:
			self.action_save_as()
			return
		save_pixbuf_at(self.main_pixbuf, fn)
		self.initial_save()

	def action_save_as(self, *args):
		gfile = self.file_chooser_save('')
		if gfile is not None:
			self.gfile = gfile
		self.action_save()

	def try_load_file(self):
		if self.get_file_path() is None:
			return
		else:
			self.main_pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.get_file_path())
			self.initial_save()

	def confirm_save_modifs(self):
		if not self._is_saved:
			fn = self.get_file_path()
			if fn is None:
				title_label = _("Untitled") + '.png'
			else:
				title_label = fn.split('/')[-1]
			dialog = Gtk.MessageDialog(modal=True, title=title_label, transient_for=self)
			dialog.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
			dialog.add_button(_("Discard"), Gtk.ResponseType.NO)
			dialog.add_button(_("Save"), Gtk.ResponseType.APPLY)
			dialog.get_message_area().add(Gtk.Label(label=_("There are unsaved modifications to your drawing.")))
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
		file_path = None
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

		if file_type == 'png':
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
			save_pixbuf_at(self.main_pixbuf, gfile.get_path())

	# HISTORY MANAGEMENT

	def action_undo(self, *args):
		should_undo = not self.active_tool().give_back_control()
		if should_undo and self.can_undo():
			self.redo_history.append(self.main_pixbuf.copy())
			self.main_pixbuf = self.undo_history.pop()
			self.use_stable_pixbuf()
			self.update_history_sensitivity()
		self.drawing_area.queue_draw()

	def action_redo(self, *args):
		self.undo_history.append(self.main_pixbuf.copy())
		self.main_pixbuf = self.redo_history.pop()
		self.use_stable_pixbuf()
		self.drawing_area.queue_draw()
		self.update_history_sensitivity()

	def update_history_sensitivity(self):
		# This line makes sense but it forbids undoing a non-finished operation
		# self.lookup_action('undo').set_enabled(self.can_undo())

		self.lookup_action('redo').set_enabled(len(self.redo_history) != 0)

	def add_operation_to_history(self, operation):
		print('todo')

	def on_tool_finished(self):
		self.undo_history.append(self.main_pixbuf.copy())
		self.redo_history = []
		self.update_history_sensitivity()
		self.drawing_area.queue_draw()
		self.set_surface_as_stable_pixbuf()
		self.active_tool().update_actions_state()

	def can_undo(self):
		if len(self.undo_history) == 0:
			return False
		else:
			return True

	# DRAWING OPERATIONS

	def on_draw(self, area, cairo_context):
		x, y = self.get_main_coord()
		self.active_tool().on_draw(area, cairo_context, x, y)

	def on_press_on_area(self, area, event):
		if event.button == 2:
			self.is_clicked = False
			self.action_exchange_color()
			return
		self.is_clicked = True
		self._is_saved = False
		x, y = self.get_main_coord()
		self.active_tool().on_press_on_area(area, event, self.surface, \
			self.size_setter.get_value(), \
			self.color_popover_l.color_widget.get_rgba(), \
			self.color_popover_r.color_widget.get_rgba(), \
			x + event.x, \
			y + event.y )

	def on_motion_on_area(self, area, event):
		if not self.is_clicked:
			return
		x, y = self.get_main_coord()
		event_x = x + event.x
		event_y = y + event.y
		self.active_tool().on_motion_on_area(area, event, self.surface, event_x, event_y)
		self.drawing_area.queue_draw()

	def on_release_on_area(self, area, event):
		if not self.is_clicked:
			return
		self.is_clicked = False
		x, y = self.get_main_coord()
		event_x = x + event.x
		event_y = y + event.y
		self.active_tool().on_release_on_area(area, event, self.surface, event_x, event_y)
		self.set_picture_title()

	def on_scroll_on_area(self, area, event):
		self.minimap.add_deltas(event.delta_x, event.delta_y, 10)

	def get_main_coord(self, *args):
		return self.minimap.preview_x, self.minimap.preview_y

	# COLORS

	def build_color_buttons(self):
		white = Gdk.RGBA(red=1.0, green=1.0, blue=1.0, alpha=1.0)
		black = Gdk.RGBA(red=0.0, green=0.0, blue=0.0, alpha=1.0)
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
		options_menu = self.app.get_menubar().get_item_link(5, Gio.MENU_LINK_SUBMENU)
		if model is None:
			options_menu.remove_all()
		else:
			options_menu.remove_all()
			options_menu.append_section(None, model)
		if widget is not None:
			self.options_btn.set_popover(widget)
		elif model is not None:
			self.options_btn.set_menu_model(model)
		else:
			self.options_btn.set_popover(None)
		self.update_option_label()

	def update_option_label(self, *args):
		self.options_label.set_label(self.active_tool().get_options_label())

	# PRINTING

	def action_print(self, *args):
		op = Gtk.PrintOperation()
		op.connect('draw-page', self.do_draw_page)
		op.connect('begin-print', self.do_begin_print)
		op.connect('end-print', self.do_end_print)
		res = op.run(Gtk.PrintOperationAction.PRINT_DIALOG, self)

	def do_end_print(self, *args):
		pass

	def do_draw_page(self, operation, print_ctx, page_num):
		Gdk.cairo_set_source_pixbuf(print_ctx.get_cairo_context(), self.main_pixbuf, 0, 0)
		print_ctx.get_cairo_context().paint()
		op.set_n_pages(1)

	def do_begin_print(self, op, print_ctx):
		Gdk.cairo_set_source_pixbuf(print_ctx.get_cairo_context(), self.main_pixbuf, 0, 0)
		print_ctx.get_cairo_context().paint()
		op.set_n_pages(1)

	# MAIN_PIXBUF-RELATED METHODS

	def edit_properties(self, *args):
		DrawingPropertiesDialog(self)

	def get_pixbuf_width(self):
		return self.main_pixbuf.get_width()

	def get_pixbuf_height(self):
		return self.main_pixbuf.get_height()

	def get_surface(self):
		return self.surface

	def set_surface_as_stable_pixbuf(self):
		self.main_pixbuf = Gdk.pixbuf_get_from_surface(self.surface, 0, 0, \
			self.surface.get_width(), self.surface.get_height())

	def use_stable_pixbuf(self):
		self.surface = Gdk.cairo_surface_create_from_pixbuf(self.main_pixbuf, 0, None)

	def show_overlay_on_surface(self, surface, cairo_path): # TODO doit être utilisé ailleurs
		w_context = cairo.Context(surface)
		w_context.new_path()
		w_context.append_path(cairo_path)
		w_context.clip_preserve()
		w_context.set_source_rgba(0.1, 0.1, 0.3, 0.2)
		w_context.paint()
		w_context.set_source_rgba(0.5, 0.5, 0.5, 0.5)
		w_context.stroke()

	def scale_pixbuf_to(self, new_width, new_height): # XXX c'est nul
		self.main_pixbuf = self.main_pixbuf.scale_simple(new_width, new_height, GdkPixbuf.InterpType.TILES)
		self.use_stable_pixbuf()
		self.on_tool_finished()

	def rotate_pixbuf(self, angle): # XXX c'est nul
		self.main_pixbuf = self.main_pixbuf.rotate_simple(angle)
		self.use_stable_pixbuf()
		self.on_tool_finished()

