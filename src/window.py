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

from .pencil import ToolPencil
from .select import ToolSelect
from .line import ToolLine
from .paint import ToolPaint
from .text import ToolText
from .picker import ToolPicker
from .shape import ToolShape
from .eraser import ToolEraser
from .polygon import ToolPolygon

from .pixbuf_manager import DrawingPixbufManager

from .properties import DrawingPropertiesDialog
from .crop_dialog import DrawingCropDialog
from .scale_dialog import DrawingScaleDialog
from .rotate_dialog import DrawingRotateDialog

@GtkTemplate(ui='/com/github/maoschanz/Drawing/ui/window.ui')
class DrawingWindow(Gtk.ApplicationWindow):
	__gtype_name__ = 'DrawingWindow'

	_settings = Gio.Settings.new('com.github.maoschanz.Drawing')

	paned_area = GtkTemplate.Child()
	tools_panel = GtkTemplate.Child()
	toolbar_box = GtkTemplate.Child()
	drawing_area = GtkTemplate.Child()
	bottom_panel = GtkTemplate.Child()
	color_btn_l = GtkTemplate.Child()
	color_btn_r = GtkTemplate.Child()
	options_btn = GtkTemplate.Child()
	options_label = GtkTemplate.Child()
	options_long_box = GtkTemplate.Child()
	options_short_box = GtkTemplate.Child()
	size_setter = GtkTemplate.Child()
	minimap_btn = GtkTemplate.Child()
	minimap_icon = GtkTemplate.Child()
	minimap_label = GtkTemplate.Child()
	tool_info_label = GtkTemplate.Child() # TODO

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.init_template()
		self.init_instance_attributes()

		decorations = self._settings.get_string('decorations')
		self.set_ui_bars(decorations)
		self.set_picture_title(None)
		self.maximize()

		self.add_all_win_actions()

		self.color_btn_l.set_rgba(Gdk.RGBA(red=0.0, green=0.0, blue=0.0, alpha=1.0))
		self.color_btn_r.set_rgba(Gdk.RGBA(red=1.0, green=1.0, blue=1.0, alpha=1.0))
		self.set_palette_setting()

		self.build_minimap()
		self._pixbuf_manager = DrawingPixbufManager(self)

		self.minimap_area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | \
			Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.POINTER_MOTION_MASK)
		self.drawing_area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | \
			Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.POINTER_MOTION_MASK)

		self.app = kwargs['application']
		self.init_tools()

		self.build_options_popover()
		self.update_size_spinbtn_state(self.active_tool().use_size)

		self.update_history_sensitivity()
		self.connect_signals()

		self._pixbuf_manager.reset_selection()
		self.init_background()

	def init_instance_attributes(self):
		self.handlers = []
		self._is_saved = True
		self.active_tool_id = 'pencil'
		self.former_tool_id = 'pencil'
		self.tool_width = 10
		self.is_clicked = False
		self.minimap_area = None
		self.header_bar = None
		self.main_menu_btn = None

	def init_tools(self):
		self.tools = {}
		self.tools['pencil'] = ToolPencil(self)
		self.tools['select'] = ToolSelect(self)
		self.tools['eraser'] = ToolEraser(self)
		self.tools['text'] = ToolText(self)
		self.tools['picker'] = ToolPicker(self)
		if self._settings.get_boolean('experimental'):
			self.tools['paint'] = ToolPaint(self)
		self.tools['line'] = ToolLine(self)
		self.tools['shape'] = ToolShape(self)
		self.tools['polygon'] = ToolPolygon(self)

		# Side panel
		self.build_tool_rows()
		self.tools_panel.show_all()
		self.full_panel_width = self.tools_panel.get_preferred_width()[0]
		self.set_tools_labels_visibility(False)
		self.icon_panel_width = self.tools_panel.get_preferred_width()[0]
		self.paned_area.set_position(0)

		# Global menubar
		if not self.app.has_tools_in_menubar:
			tools_menu = Gio.Menu()
			for tool_id in self.tools:
				self.tools[tool_id].add_item_to_menu(tools_menu)
			self.app.add_tools_to_menubar(tools_menu)

	def init_background(self, *args):
		w_context = cairo.Context(self._pixbuf_manager.surface)
		r = float(self._settings.get_strv('default-rgba')[0])
		g = float(self._settings.get_strv('default-rgba')[1])
		b = float(self._settings.get_strv('default-rgba')[2])
		a = float(self._settings.get_strv('default-rgba')[3])
		w_context.set_source_rgba(r, g, b, a)
		w_context.paint()
		self._pixbuf_manager.set_pixbuf_as_stable()
		self._pixbuf_manager.update_minimap()

	def initial_save(self, fn):
		self.set_picture_title(fn)
		self._is_saved = True
		self._pixbuf_manager.initial_save(fn)
		self.lookup_action('open_with').set_enabled(True)

	def action_close(self, *args):
		self.close()

	def on_close(self, *args):
		return not self.confirm_save_modifs()

	# GENERAL PURPOSE METHODS

	def connect_signals(self):
		self.handlers.append( self.connect('delete-event', self.on_close) )

		self.handlers.append( self.size_setter.connect('change-value', self.update_size_spinbtn_value) )
		self.handlers.append( self.options_btn.connect('toggled', self.update_option_label) )

		self.handlers.append( self.drawing_area.connect('draw', self.on_draw) )
		self.handlers.append( self.drawing_area.connect('motion-notify-event', self.on_motion_on_area) )
		self.handlers.append( self.drawing_area.connect('button-press-event', self.on_press_on_area) )
		self.handlers.append( self.drawing_area.connect('button-release-event', self.on_release_on_area) )

		self.handlers.append( self.minimap_area.connect('draw', self.on_minimap_draw) )
		# self.handlers.append( self.minimap_area.connect('motion-notify-event', self.on_minimap_motion) )
		self.handlers.append( self.minimap_area.connect('button-press-event', self.on_minimap_press) )
		self.handlers.append( self.minimap_area.connect('button-release-event', self.on_minimap_release) )

		self.handlers.append( self.tools_panel.connect('size-allocate', self.update_tools_visibility) )
		self.set_tools_labels_visibility(self._settings.get_boolean('panel-width'))

		self.handlers.append( self.connect('configure-event', self.adapt_to_window_size) )

		# Settings
		self.handlers.append( self._settings.connect('changed::direct-color-edit', self.set_palette_setting) )
		# TODO..

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
		self.add_action_simple('main_color', self.action_main_color)
		self.add_action_simple('secondary_color', self.action_secondary_color)
		self.add_action_simple('exchange_color', self.action_exchange_color)

		self.add_action_simple('open_with', self.action_open_with)
		self.lookup_action('open_with').set_enabled(False)
		self.add_action_simple('print', self.action_print)

		self.add_action_simple('pic_crop', self.action_crop)
		self.add_action_simple('pic_scale', self.action_scale)
		# self.add_action_simple('pic_rotate', self.action_rotate)
		self.add_action_simple('properties', self.edit_properties)

		if self.main_menu_btn is not None:
			self.add_action_simple('main_menu', self.action_main_menu)

		self.add_action_simple('toggle_preview', self.action_toggle_preview)
		self.add_action_simple('bigger_preview', self.action_bigger_preview)
		self.add_action_simple('smaller_preview', self.action_smaller_preview)

		self.add_action_simple('close', self.action_close)
		self.add_action_simple('save', self.action_save)
		self.add_action_simple('undo', self.action_undo)
		self.add_action_simple('redo', self.action_redo)

		self.add_action_simple('save_as', self.action_save_as)
		self.add_action_simple('exp_png', self.export_as_png)
		self.add_action_simple('exp_jpeg', self.export_as_jpeg)
		self.add_action_simple('exp_bmp', self.export_as_bmp)

		self.add_action_enum('active_tool', 'pencil', self.on_change_active_tool)

	def update_selection_actions(self, state):
		if not 'select' in self.tools:
			return
		self.lookup_action('unselect').set_enabled(state)
		self.lookup_action('cut').set_enabled(state)
		self.lookup_action('copy').set_enabled(state)
		self.lookup_action('selection_delete').set_enabled(state)
		self.lookup_action('selection_crop').set_enabled(state)
		self.lookup_action('selection_resize').set_enabled(state)
		# self.lookup_action('selection_rotate').set_enabled(state)
		self.lookup_action('selection_export').set_enabled(state)

	def adapt_to_window_size(self,*args):
		available_width = self.options_long_box.get_preferred_width()[0] + \
			self.options_short_box.get_preferred_width()[0] + \
			self.tool_info_label.get_allocated_width() + \
			self.minimap_btn.get_allocated_width()

		used_width = self.options_long_box.get_allocated_width() + \
			self.options_short_box.get_allocated_width() + \
			self.tool_info_label.get_preferred_width()[0] + \
			self.minimap_btn.get_preferred_width()[0]

		if used_width > 0.9*available_width:
			self.options_long_box.set_visible(False)
			self.options_short_box.set_visible(True)
			self.minimap_label.set_visible(False)
			self.minimap_icon.set_visible(True)
		else:
			self.options_short_box.set_visible(False)
			self.options_long_box.set_visible(True)
			self.minimap_label.set_visible(True)
			self.minimap_icon.set_visible(False)

	# WINDOW BARS

	def set_picture_title(self, fn):
		if fn is None:
			fn = _("Unsaved file")
		self.set_title(_("Drawing") + ' - ' + fn)
		if self.header_bar is not None:
			self.header_bar.set_subtitle(fn)
			self.header_bar.set_title(_("Drawing"))

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
		builder = Gtk.Builder()
		builder.add_from_resource("/com/github/maoschanz/Drawing/ui/toolbar.ui")
		toolbar = builder.get_object("toolbar")
		self.toolbar_box.add(toolbar)
		self.toolbar_box.show_all()

	def build_headerbar(self):
		builder = Gtk.Builder()
		builder.add_from_resource("/com/github/maoschanz/Drawing/ui/headerbar.ui")
		self.header_bar = builder.get_object("header_bar")
		save_as_btn = builder.get_object("save_as_btn")
		self.main_menu_btn = builder.get_object("main_menu_btn")

		builder.add_from_resource("/com/github/maoschanz/Drawing/ui/menus.ui")
		main_menu = builder.get_object("window-menu")
		menu_popover = Gtk.Popover.new_from_model(self.main_menu_btn, main_menu)
		self.main_menu_btn.set_popover(menu_popover)
		save_as_menu = builder.get_object("save-as-menu")
		save_as_popover = Gtk.Popover.new_from_model(save_as_btn, save_as_menu)
		save_as_btn.set_popover(save_as_popover)

	def action_main_menu(self, *args):
		self.main_menu_btn.set_active(not self.main_menu_btn.get_active())

	# MINIMAP

	def action_toggle_preview(self, *args):
		self.minimap_btn.set_active(not self.minimap_btn.get_active())

	def action_smaller_preview(self, *args):
		size = max(200, self._settings.get_int('preview-size') - 40)
		self._settings.set_int('preview-size', size)
		self._pixbuf_manager.preview_size = size
		self._pixbuf_manager.update_minimap()

	def action_bigger_preview(self, *args):
		size = self._settings.get_int('preview-size') + 40
		self._settings.set_int('preview-size', size)
		self._pixbuf_manager.preview_size = size
		self._pixbuf_manager.update_minimap()

	def build_minimap(self):
		builder = Gtk.Builder()
		builder.add_from_resource("/com/github/maoschanz/Drawing/ui/minimap.ui")
		box = builder.get_object("minimap_box")
		self.minimap_area = builder.get_object("minimap_area")
		self.minimap_area.set_size(200, 200)
		minimap_popover = Gtk.Popover()
		minimap_popover.add(box)
		self.minimap_btn.set_popover(minimap_popover)

	def on_minimap_draw(self, area, cairo_context):
		cairo_context.set_source_surface(self._pixbuf_manager.mini_surface, 0, 0)
		cairo_context.paint()

	def on_minimap_press(self, area, event):
		self._pixbuf_manager.on_minimap_press(event.x, event.y)

	def on_minimap_release(self, area, event):
		self._pixbuf_manager.on_minimap_release(event.x, event.y)

	# TOOLS PANEL

	def build_tool_rows(self):
		group = None
		for tool_id in self.tools:
			if group is None:
				group = self.tools[tool_id].row
			else:
				self.tools[tool_id].row.join_group(group)
			self.tools_panel.add(self.tools[tool_id].row)

	def set_tools_labels_visibility(self, visible):
		if visible:
			self.tools_panel.show_all()
			self.paned_area.set_position(self.tools_panel.get_preferred_width()[0]+10)
		else:
			for label in self.tools:
				self.tools[label].label_widget.set_visible(False)

	def update_tools_visibility(self, panelbox, gdkrect):
		if gdkrect.width <= self.icon_panel_width+10 \
		or gdkrect.width == self.full_panel_width \
		or gdkrect.width == self.full_panel_width+10:
			return
		if gdkrect.width >= self.full_panel_width:
			self.set_tools_labels_visibility(True)
			self._settings.set_boolean('panel-width', True)
		else:
			self.set_tools_labels_visibility(False)
			self._settings.set_boolean('panel-width', False)

	# COLORS

	def set_palette_setting(self, *args):
		color_btn_show_editor = self._settings.get_boolean('direct-color-edit')
		self.color_btn_l.props.show_editor = color_btn_show_editor
		self.color_btn_r.props.show_editor = color_btn_show_editor

	def action_main_color(self, *args):
		self.color_btn_l.activate()

	def action_secondary_color(self, *args):
		self.color_btn_r.activate()

	def action_exchange_color(self, *args):
		left_c = self.color_btn_l.get_rgba()
		self.color_btn_l.set_rgba(self.color_btn_r.get_rgba())
		self.color_btn_r.set_rgba(left_c)

	# TOOLS OPTIONS

	def update_size_spinbtn_state(self, sensitivity):
		self.size_setter.set_sensitive(sensitivity)

	def update_size_spinbtn_value(self, *args):
		self.tool_width = int(args[2])

	def build_options_popover(self):
		self.options_btn.set_popover(self.active_tool().get_options_widget())
		self.update_option_label()

	def update_option_label(self, *args):
		self.options_label.set_label(self.active_tool().get_options_label())

	def on_change_active_tool(self, *args):
		state_as_string = args[1].get_string()
		if state_as_string == args[0].get_state().get_string():
			return
		if self.tools[state_as_string].row.get_active():
			args[0].set_state(GLib.Variant.new_string(state_as_string))
		else:
			self.tools[state_as_string].row.set_active(True)
		self.former_tool_id = self.active_tool_id
		self.former_tool().give_back_control()
		self.drawing_area.queue_draw()
		self.active_tool_id = state_as_string
		self.build_options_popover()
		self.adapt_to_window_size()
		self.update_size_spinbtn_state(self.active_tool().use_size)

	def active_tool(self):
		return self.tools[self.active_tool_id]

	def former_tool(self):
		return self.tools[self.former_tool_id]

	# FILE MANAGEMENT

	def get_file_path(self):
		if self._pixbuf_manager.gfile is None:
			return None
		else:
			return self._pixbuf_manager.gfile.get_path()

	def action_save(self, *args):
		fn = self.get_file_path()
		if fn is None:
			fn = self.run_save_file_chooser('')
		self.save_pixbuf_to_fn(fn)

	def action_save_as(self, *args):
		fn = self.run_save_file_chooser('')
		self.save_pixbuf_to_fn(fn)

	def load_fn_to_pixbuf(self, fn):
		if fn is not None:
			self._pixbuf_manager.load_main_from_filename(fn)
			self.initial_save(fn)

	def save_pixbuf_to_fn(self, fn):
		if fn is not None:
			self._pixbuf_manager.save_pixbuf_to_filename(fn)
			self.initial_save(fn)

	def try_load_file(self, fn):
		# We don't want to load too big images, because the technical
		# limitations of cairo make impossible to zoom out, or to scroll.
		w = self.drawing_area.get_allocated_width()
		h = self.drawing_area.get_allocated_height()
		self._pixbuf_manager.selection_pixbuf = GdkPixbuf.Pixbuf.new_from_file(fn)
		pic_w = self._pixbuf_manager.selection_pixbuf.get_width()
		pic_h = self._pixbuf_manager.selection_pixbuf.get_height()
		if (w < pic_w) or (h < pic_h):
			title_label = _("Sorry, this picture is too big for this app!")
			dialog = Gtk.MessageDialog(modal=True, title=title_label, transient_for=self)
			# dialog.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
			dialog.add_button(_("Edit it anyway"), Gtk.ResponseType.NO)
			dialog.add_button(_("Scale it"), Gtk.ResponseType.APPLY)
			dialog.add_button(_("Crop it"), Gtk.ResponseType.YES)
			dialog.get_message_area().add(Gtk.Label(label=_("What would you prefer?")))
			dialog.show_all()
			result = dialog.run()

			if result == Gtk.ResponseType.APPLY: # Scale it
				if pic_w/pic_h > w/h:
					self._pixbuf_manager.main_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(fn, w, -1, True)
				else:
					self._pixbuf_manager.main_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(fn, -1, h, True)
				self.initial_save(fn)
			elif result == Gtk.ResponseType.YES: # Crop it
				self._pixbuf_manager.load_main_from_filename(fn)
				crop_dialog = DrawingCropDialog(self, True, True)
				result2 = crop_dialog.run()
				if result2 == Gtk.ResponseType.APPLY:
					self.initial_save(fn)
					crop_dialog.on_apply()
				else:
					crop_dialog.on_cancel()
			else:
				self.load_fn_to_pixbuf(fn) # Edit it anyway
			dialog.destroy()
		else:
			self.load_fn_to_pixbuf(fn)

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

	def run_save_file_chooser(self, file_type):
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
			file_path = file_chooser.get_filename()
		file_chooser.destroy()
		return file_path

	def export_as_png(self, *args):
		self._pixbuf_manager.export_main_as('png')

	def export_as_jpeg(self, *args):
		self._pixbuf_manager.export_main_as('jpeg')

	def export_as_bmp(self, *args):
		self._pixbuf_manager.export_main_as('bmp')

	def action_open_with(self, *args):
		os.system('xdg-open ' + self.get_file_path())

	# HISTORY MANAGEMENT

	def action_undo(self, *args):
		should_undo = not self.active_tool().give_back_control()
		if should_undo and self._pixbuf_manager.can_undo():
			self._pixbuf_manager.undo_operation()
			self.update_history_sensitivity()
		self.drawing_area.queue_draw()

	def action_redo(self, *args):
		self._pixbuf_manager.redo_operation()
		self.drawing_area.queue_draw()
		self.update_history_sensitivity()

	def update_history_sensitivity(self):
		# This line makes sense but it forbids undoing a non-finished operation
		# self.lookup_action('undo').set_enabled(self._pixbuf_manager.can_undo())
		self.lookup_action('redo').set_enabled(self._pixbuf_manager.can_redo())

	# DRAWING OPERATIONS

	def on_draw(self, area, cairo_context):
		# Ça marche mais je ne sais pas si avoir une surface ne serait pas mieux.
		# Gdk.cairo_set_source_pixbuf(cairo_context, self._pixbuf_manager.main_pixbuf, 0, 0)

		# Ça marche aussi mais c'est moins idéal complexitivement.
		# surface = Gdk.cairo_surface_create_from_pixbuf(self._pixbuf_manager.main_pixbuf, 0, None)

		cairo_context.set_source_surface(self._pixbuf_manager.surface, 0, 0)
		cairo_context.paint()

	def on_motion_on_area(self, area, event):
		if (not self.is_clicked):
			return
		self.active_tool().on_motion_on_area(area, event, self._pixbuf_manager.surface)
		self.drawing_area.queue_draw()

	def on_press_on_area(self, area, event):
		self._is_saved = False
		self.is_clicked = True
		self.x_press = event.x
		self.y_press = event.y
		self.tool_width = int(self.size_setter.get_value())

		if event.button is 2:
			self.action_exchange_color()
			self.is_clicked = False
			return

		self.active_tool().on_press_on_area(area, event, self._pixbuf_manager.surface, \
			self.size_setter.get_value(), self.color_btn_l.get_rgba(), self.color_btn_r.get_rgba())

	def on_release_on_area(self, area, event):
		if not self.is_clicked:
			return
		self.is_clicked = False
		self.active_tool().on_release_on_area(area, event, self._pixbuf_manager.surface)

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
		Gdk.cairo_set_source_pixbuf(print_ctx.get_cairo_context(), self._pixbuf_manager.main_pixbuf, 0, 0)
		print_ctx.get_cairo_context().paint()
		op.set_n_pages(1)

	def do_begin_print(self, op, print_ctx):
		Gdk.cairo_set_source_pixbuf(print_ctx.get_cairo_context(), self._pixbuf_manager.main_pixbuf, 0, 0)
		print_ctx.get_cairo_context().paint()
		op.set_n_pages(1)

	# MAIN_PIXBUF-RELATED METHODS

	def edit_properties(self, *args):
		DrawingPropertiesDialog(self)

	def action_crop(self, *args):
		crop_dialog = DrawingCropDialog(self, False, False)
		result = crop_dialog.run()
		if result == Gtk.ResponseType.APPLY:
			crop_dialog.on_apply()
		else:
			crop_dialog.on_cancel()

	def action_scale(self, *args):
		self.scale_pixbuf(False)

	def action_rotate(self, *args): # TODO
		rotate_dialog = DrawingRotateDialog(self, 0, 0, False)
		result = rotate_dialog.run()
		if result == Gtk.ResponseType.APPLY:
			rotate_dialog.on_apply()
		else:
			rotate_dialog.on_cancel()
		pass

	def scale_pixbuf(self, is_selection):
		if is_selection:
			w = self._pixbuf_manager.selection_pixbuf.get_width()
			h = self._pixbuf_manager.selection_pixbuf.get_height()
		else:
			w = self.get_pixbuf_width()
			h = self.get_pixbuf_height()
		scale_dialog = DrawingScaleDialog(self, w, h, is_selection)
		result = scale_dialog.run()
		if result == Gtk.ResponseType.APPLY:
			scale_dialog.on_apply()
		else:
			scale_dialog.on_cancel()

	def get_pixbuf_width(self):
		return self._pixbuf_manager.main_pixbuf.get_width()

	def get_pixbuf_height(self):
		return self._pixbuf_manager.main_pixbuf.get_height()

	def get_surface(self):
		return self._pixbuf_manager.surface

