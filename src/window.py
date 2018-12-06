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
import cairo

from gettext import gettext as _

from .gi_composites import GtkTemplate

from .pencil import ToolPencil
from .select import ToolSelect
from .line import ToolLine
from .paint import ToolPaint
from .text import ToolText
from .picker import ToolPicker
from .shape import ToolShape
from .eraser import ToolEraser

DEV_VERSION = False

from .pixbuf_manager import DrawingPixbufManager

from .properties import DrawingPropertiesDialog
from .crop_dialog import DrawingCropDialog
from .scale_dialog import DrawingScaleDialog

SETTINGS_SCHEMA = 'com.github.maoschanz.Drawing'

@GtkTemplate(ui='/com/github/maoschanz/Drawing/ui/window.ui')
class DrawingWindow(Gtk.ApplicationWindow):
	__gtype_name__ = 'DrawingWindow'

	_file_path = None
	_is_saved = True
	active_tool_id = 'pencil'
	former_tool_id = 'pencil'
	tool_width = 10
	is_clicked = False
	window_has_control = True
	options_popover = None

	paned_area = GtkTemplate.Child()
	tools_panel = GtkTemplate.Child()
	tools = {}

	toolbar_box = GtkTemplate.Child()
	header_bar = None
	primary_menu_btn = None

	drawing_area = GtkTemplate.Child()

	color_btn_l = GtkTemplate.Child()
	color_btn_r = GtkTemplate.Child()
	options_btn = GtkTemplate.Child()
	options_label = GtkTemplate.Child()
	options_long_box = GtkTemplate.Child()
	options_short_box = GtkTemplate.Child()
	size_setter = GtkTemplate.Child()
	tool_info_label = GtkTemplate.Child() # TODO

	handlers = []

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.init_template()

		self._settings = Gio.Settings.new(SETTINGS_SCHEMA)
		decorations = self._settings.get_string('decorations')
		DEV_VERSION = self._settings.get_boolean('experimental')
		self.set_ui_bars(decorations)
		self.set_picture_title(None)
		self.maximize()

		self.color_btn_l.set_rgba(Gdk.RGBA(red=0.0, green=0.0, blue=0.0, alpha=1.0))
		self.color_btn_r.set_rgba(Gdk.RGBA(red=1.0, green=1.0, blue=1.0, alpha=1.0))
		self.set_palette_setting()

		self._pixbuf_manager = DrawingPixbufManager(self)

		self.drawing_area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | \
			Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.POINTER_MOTION_MASK)

		self.tools['pencil'] = ToolPencil(self)
		self.tools['select'] = ToolSelect(self)
		self.tools['eraser'] = ToolEraser(self)
		self.tools['text'] = ToolText(self)
		self.tools['picker'] = ToolPicker(self)
		if DEV_VERSION:
			self.tools['paint'] = ToolPaint(self)
		self.tools['line'] = ToolLine(self)
		self.tools['shape'] = ToolShape(self)
		self.build_tool_rows()
		self.tools_panel.show_all()
		self.update_tools_visibility_for_width(self.tools_panel, self._settings.get_int('panel-width'))
		self.paned_area.set_position(self._settings.get_int('panel-width') + 10)

		self.app = kwargs['application']
		if not self.app.has_tools_in_menubar:
			tools_menu = Gio.Menu()
			for tool_id in self.tools:
				self.tools[tool_id].add_item_to_menu(tools_menu)
			self.app.add_tools_to_menubar(tools_menu)

		self.build_options_popover()
		self.update_size_spinbtn_state(self.active_tool().use_size)

		self.add_all_win_actions()
		self.connect_signals()
		self.init_background()

	def init_background(self, *args):
		w_context = cairo.Context(self._pixbuf_manager.surface)
		r = float(self._settings.get_strv('default-rgba')[0])
		g = float(self._settings.get_strv('default-rgba')[1])
		b = float(self._settings.get_strv('default-rgba')[2])
		a = float(self._settings.get_strv('default-rgba')[3])
		w_context.set_source_rgba(r, g, b, a)
		w_context.paint()
		self._pixbuf_manager.set_pixbuf_as_stable()

	def is_empty_picture(self):
		if self._file_path is None and not self._pixbuf_manager.can_undo():
			return True
		else:
			return False

	def initial_save(self):
		self.set_picture_title(self._file_path)
		self._is_saved = True
		self._pixbuf_manager.use_stable_pixbuf()

	def action_close(self, *args):
		self.close()

	def on_close(self, *args):
		return not self.confirm_save_modifs()

	# GENERAL PURPOSE METHODS

	def connect_signals(self):
		self.handlers.append( self.connect('delete-event', self.on_close) )

		self.handlers.append( self.size_setter.connect('change-value', self.update_size_spinbtn_value) )

		self.handlers.append( self.drawing_area.connect('draw', self.on_draw) )
		self.handlers.append( self.drawing_area.connect('configure-event', self.on_configure) )

		self.handlers.append( self.drawing_area.connect('motion-notify-event', self.on_motion_on_area) )
		self.handlers.append( self.drawing_area.connect('button-press-event', self.on_press_on_area) )
		self.handlers.append( self.drawing_area.connect('button-release-event', self.on_release_on_area) )
		self.handlers.append( self.drawing_area.connect('key-press-event', self.on_key_on_area) )

		self.handlers.append( self.tools_panel.connect('size-allocate', self.update_tools_visibility) )
		self.handlers.append( self.connect('size-allocate', self.update_options_box) )

		# Settings
		self.handlers.append( self._settings.connect('changed::direct-color-edit', self.set_palette_setting) )
		# TODO..

	def add_action_like_a_boss(self, action_name, callback):
		action = Gio.SimpleAction.new(action_name, None)
		action.connect("activate", callback)
		self.add_action(action)

	def add_all_win_actions(self):
		# self.add_action_like_a_boss("cut", self.action_cut)
		# self.add_action_like_a_boss("copy", self.action_copy)
		# self.add_action_like_a_boss("selection_delete", self.action_selection_delete)
		# self.add_action_like_a_boss("selection_resize", self.action_selection_resize)
		# self.add_action_like_a_boss("selection_rotate", self.action_selection_rotate)
		# self.add_action_like_a_boss("selection_export", self.action_selection_export)

		# self.add_action_like_a_boss("import", self.action_import_png)
		# self.add_action_like_a_boss("paste", self.action_paste)
		# self.add_action_like_a_boss("select_all", self.action_select_all)
		# self.add_action_like_a_boss("unselect", self.action_unselect)

		self.add_action_like_a_boss("primary_color", self.action_primary_color)
		self.add_action_like_a_boss("secondary_color", self.action_secondary_color)
		self.add_action_like_a_boss("exchange_color", self.action_exchange_color)

		# self.add_action_like_a_boss("send_to", self.action_send_to)
		self.add_action_like_a_boss("print", self.action_print)

		self.add_action_like_a_boss("crop", self.action_crop)
		self.add_action_like_a_boss("scale", self.action_scale)
		self.add_action_like_a_boss("properties", self.edit_properties)

		if self.primary_menu_btn is not None:
			self.add_action_like_a_boss("primary_menu", self.action_primary_menu)

		self.add_action_like_a_boss("close", self.action_close)
		self.add_action_like_a_boss("save", self.action_save)
		self.add_action_like_a_boss("undo", self.action_undo)
		self.add_action_like_a_boss("redo", self.action_redo)
		self.update_history_sensitivity()

		self.add_action_like_a_boss("save_as", self.action_save_as)
		self.add_action_like_a_boss("exp_png", self.export_as_png)
		self.add_action_like_a_boss("exp_jpeg", self.export_as_jpeg)
		self.add_action_like_a_boss("exp_bmp", self.export_as_bmp)

		action_active_tool = Gio.SimpleAction().new_stateful('active_tool', \
			GLib.VariantType.new('s'), GLib.Variant.new_string('pencil'))
		action_active_tool.connect('change-state', self.on_change_active_tool)
		self.add_action(action_active_tool)

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
		elif decorations == 'csd-menubar':
			self.build_headerbar()
			self.set_titlebar(self.header_bar)
			self.set_show_menubar(True)
			self.build_toolbar()
		else:
			self.build_toolbar()

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
		self.primary_menu_btn = builder.get_object("primary_menu_btn")

		builder.add_from_resource("/com/github/maoschanz/Drawing/ui/menus.ui")
		primary_menu = builder.get_object("window-menu")
		menu_popover = Gtk.Popover.new_from_model(self.primary_menu_btn, primary_menu)
		self.primary_menu_btn.set_popover(menu_popover)
		save_as_menu = builder.get_object("save-as-menu")
		save_as_popover = Gtk.Popover.new_from_model(save_as_btn, save_as_menu)
		save_as_btn.set_popover(save_as_popover)

	def action_primary_menu(self, *args):
		self.primary_menu_btn.set_active(not self.primary_menu_btn.get_active())

	# TOOLS

	def build_tool_rows(self):
		group = None
		for tool_id in self.tools:
			if group is None:
				group = self.tools[tool_id].row
			else:
				self.tools[tool_id].row.join_group(group)
			self.tools_panel.add(self.tools[tool_id].row)
		self.full_panel_width = 0

	def update_tools_visibility(self, listbox, gdkrectangle):
		self.update_tools_visibility_for_width(listbox, gdkrectangle.width)

	def update_tools_visibility_for_width(self, listbox, width):
		temp = max(self.full_panel_width, listbox.get_preferred_width()[0])
		if self.full_panel_width == temp:
			return
		self.full_panel_width = temp
		if (width < self.full_panel_width):
			self.set_tools_labels_visibility(False)
		else:
			self.set_tools_labels_visibility(True)
		self._settings.set_int('panel-width', width)

	# COLORS

	def set_palette_setting(self, *args):
		color_btn_show_editor = self._settings.get_boolean('direct-color-edit')
		self.color_btn_l.props.show_editor = color_btn_show_editor
		self.color_btn_r.props.show_editor = color_btn_show_editor

	def action_primary_color(self, *args):
		self.color_btn_l.activate()

	def action_secondary_color(self, *args):
		self.color_btn_r.activate()

	def action_exchange_color(self, *args):
		left_c = self.color_btn_l.get_rgba()
		self.color_btn_l.set_rgba(self.color_btn_r.get_rgba())
		self.color_btn_r.set_rgba(left_c)

	# TOOL OPTIONS

	def set_tools_labels_visibility(self, visible):
		for label in self.tools:
			self.tools[label].label_widget.set_visible(visible)

	def update_options_box(self, window, gdkrectangle):
		available_width = self.options_long_box.get_preferred_width()[0] + \
			self.options_short_box.get_preferred_width()[0] + \
			self.tool_info_label.get_allocated_width()

		used_width = self.options_long_box.get_allocated_width() + \
			self.options_short_box.get_allocated_width()

		if used_width > 0.9*available_width:
			self.options_long_box.set_visible(False)
			self.options_short_box.set_visible(True)
		else:
			self.options_short_box.set_visible(False)
			self.options_long_box.set_visible(True)

	def update_size_spinbtn_state(self, sensitivity):
		self.size_setter.set_sensitive(sensitivity)

	def update_size_spinbtn_value(self, *args):
		self.tool_width = int(args[2])

	# TOOLS MANAGEMENT

	def build_options_popover(self):
		if self.options_popover is not None:
			self.options_popover.destroy()
			self.options_popover = None
		if self.active_tool().use_options:
			self.options_popover = Gtk.Popover()
			self.options_box = self.active_tool().get_options_widget()
			self.options_box.show_all()
			self.options_popover.add(self.options_box)
			self.options_btn.set_popover(self.options_popover)
		self.update_option_label()

	def update_option_label(self):
		if self.active_tool().use_options:
			self.options_label.set_label(self.active_tool().get_options_label())
		else:
			self.options_label.set_label(_("No options"))

	def on_change_active_tool(self, *args):
		state_as_string = args[1].get_string()
		if state_as_string == args[0].get_state().get_string():
			return
		if self.tools[state_as_string].row.get_active():
			args[0].set_state(GLib.Variant.new_string(state_as_string))
		else:
			self.tools[state_as_string].row.set_active(True)
		self.former_tool().give_back_control()
		self.drawing_area.queue_draw()
		self.former_tool_id = self.active_tool_id
		self.active_tool_id = state_as_string
		self.build_options_popover()
		self.update_size_spinbtn_state(self.active_tool().use_size)

	def active_tool(self):
		return self.tools[self.active_tool_id]

	def former_tool(self):
		return self.tools[self.former_tool_id]

	# FILE MANAGEMENT

	def action_save(self, *args):
		fn = self._file_path
		if fn is None:
			fn = self.run_save_file_chooser('')
		self.save_pixbuf_to_fn(fn)

	def action_save_as(self, *args):
		fn = self.run_save_file_chooser('')
		self.save_pixbuf_to_fn(fn)

	def load_fn_to_pixbuf(self, fn):
		if fn is not None:
			self._pixbuf_manager.load_main_from_filename(fn)
			self._file_path = fn
			self.initial_save()

	def save_pixbuf_to_fn(self, fn):
		if fn is not None:
			self._pixbuf_manager.save_pixbuf_to_filename(fn)
			self._file_path = fn
			self.initial_save()

	def try_load_file(self, fn):
		# We don't want to load too big images, because the technical
		# limitations of cairo make impossible to zoom out, or to scroll.
		w = self.drawing_area.get_allocated_width()
		h = self.drawing_area.get_allocated_height()
		temp = GdkPixbuf.Pixbuf.new_from_file(fn)
		pic_w = temp.get_width()
		pic_h = temp.get_height()
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

			if result == Gtk.ResponseType.APPLY: # Scale it # FIXME ça scale beaucoup trop fort
				self._file_path = fn
				self._pixbuf_manager.main_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(fn, w, h, True)
				self.initial_save()
			elif result == Gtk.ResponseType.YES: # Crop it
				self._pixbuf_manager.load_main_from_filename(fn)
				crop_dialog = DrawingCropDialog(self, pic_w, pic_h, True)
				result2 = crop_dialog.run()
				if result2 == Gtk.ResponseType.APPLY:
					self._file_path = fn
					self.initial_save()
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
			if self._file_path is None:
				title_label = _("Untitled") + '.png'
			else:
				title_label = self._file_path.split('/')[-1]
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

	# HISTORY MANAGEMENT

	def action_undo(self, *args):
		self._pixbuf_manager.undo_operation()
		self.drawing_area.queue_draw()
		self.update_history_sensitivity()

	def action_redo(self, *args):
		self._pixbuf_manager.redo_operation()
		self.drawing_area.queue_draw()
		self.update_history_sensitivity()

	def update_history_sensitivity(self):
		self.lookup_action('undo').set_enabled(self._pixbuf_manager.can_undo())
		self.lookup_action('redo').set_enabled(self._pixbuf_manager.can_redo())

	# DRAWING OPERATIONS

	def on_draw(self, area, cairo_context):
		# Ça marche mais je ne sais pas si avoir une surface ne serait pas mieux.
		# Gdk.cairo_set_source_pixbuf(cairo_context, self._pixbuf_manager.main_pixbuf, 0, 0)

		# Ça marche aussi mais c'est moins idéal complexitivement.
		# surface = Gdk.cairo_surface_create_from_pixbuf(self._pixbuf_manager.main_pixbuf, 0, None)

		cairo_context.set_source_surface(self._pixbuf_manager.surface, 0, 0)
		cairo_context.paint()

	def on_configure(self, area, cairo_context):
		print("ceci est appelé quand ça dimensionne la zone?")

	def on_key_on_area(self, area, event):
		print("key") # TODO les touches sont des constantes Gdk https://github.com/GNOME/gtk/blob/master/gdk/keynames.txt
		self.active_tool().on_key_on_area(area, event, self._pixbuf_manager.surface)
		self.drawing_area.queue_draw()

	def on_motion_on_area(self, area, event):
		if (not self.is_clicked):
			return
		self.active_tool().on_motion_on_area(area, event, self._pixbuf_manager.surface)
		self.drawing_area.queue_draw()

	def on_press_on_area(self, area, event):
		self._is_saved = False
		self.window_has_control = False
		self.is_clicked = True
		self.x_press = event.x
		self.y_press = event.y
		self.tool_width = int(self.size_setter.get_value())

		if event.button is 2:
			self.on_exchange_color(None)
			self.is_clicked = False
			return

		self.active_tool().on_press_on_area(area, event, self._pixbuf_manager.surface, \
			self.size_setter.get_value(), self.color_btn_l.get_rgba(), self.color_btn_r.get_rgba())

	def on_release_on_area(self, area, event):
		if not self.is_clicked:
			return
		self.is_clicked = False

		self.active_tool().on_release_on_area(area, event, self._pixbuf_manager.surface)
		self.window_has_control = self.active_tool().window_can_take_back_control

		self.drawing_area.queue_draw()

		if self.window_has_control:
			print('release où la fenêtre a récupéré le contrôle')
			self._pixbuf_manager.on_tool_finished()

	# SELECTION-RELATED ACTIONS # TODO

	def action_import_png(self, *args):
		self.tools['select'].row.set_active(True)
		print("import")

	def action_cut(self, *args):
		print("cut")

	def action_copy(self, *args):
		print("copy")

	def action_paste(self, *args):
		self.tools['select'].row.set_active(True)
		print("paste")

	def action_select_all(self, *args):
		print("select_all")

	def action_unselect(self, *args):
		print("unselect")

	def action_selection_delete(self, *args):
		print("selection_delete")

	def action_selection_resize(self, *args):
		print("selection_resize")

	def action_selection_rotate(self, *args):
		print("selection_rotate")

	def action_selection_export(self, *args):
		print("selection_export")

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

	def action_crop(self, *args): # FIXME ça envoie pas les bonnes valeurs ?
		crop_dialog = DrawingCropDialog(self, self._pixbuf_manager.surface.get_width(), \
			self._pixbuf_manager.surface.get_height(), False)
		result = crop_dialog.run()
		if result == Gtk.ResponseType.APPLY:
			crop_dialog.on_apply()
		else:
			crop_dialog.on_cancel()

	def action_scale(self, *args):
		scale_dialog = DrawingScaleDialog(self)
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


