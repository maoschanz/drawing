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

from gi.repository import Gtk, Gdk, Gio, GdkPixbuf
import cairo

from gettext import gettext as _

from .gi_composites import GtkTemplate

from .pencil import ToolPencil
from .crop import ToolCrop
from .select import ToolSelect
from .line import ToolLine
from .paint import ToolPaint
from .text import ToolText
from .picker import ToolPicker
from .shape import ToolShape
from .eraser import ToolEraser

DEV_VERSION = False

from .properties import DrawPropertiesDialog
from .crop_dialog import DrawCropDialog

SETTINGS_SCHEMA = 'com.github.maoschanz.Draw'

@GtkTemplate(ui='/com/github/maoschanz/Draw/ui/window.ui')
class DrawWindow(Gtk.ApplicationWindow):
	__gtype_name__ = 'DrawWindow'

	header_bar = GtkTemplate.Child()
	open_btn = GtkTemplate.Child()
	save_btn = GtkTemplate.Child()
	undo_btn = GtkTemplate.Child()
	redo_btn = GtkTemplate.Child()
	menu_btn = GtkTemplate.Child()
	menu_btn_img = GtkTemplate.Child()

	tools_panel = GtkTemplate.Child()
	tools = {}
	tools_buttons = {}

	drawing_area = GtkTemplate.Child()

	color_btn_l = GtkTemplate.Child()
	color_btn_exc = GtkTemplate.Child()
	color_btn_r = GtkTemplate.Child()

	options_btn = GtkTemplate.Child()
	options_label = GtkTemplate.Child()
	options_long_box = GtkTemplate.Child()
	options_short_box = GtkTemplate.Child()

	size_setter = GtkTemplate.Child()

	tool_info_label = GtkTemplate.Child()

	undo_history = []
	redo_history = []

	handlers = []

	def __init__(self, file_path, **kwargs):
		super().__init__(**kwargs)
		self.init_template()
		self.maximize()
		
		self._file_path = file_path
		self._is_saved = True

		self._settings = Gio.Settings.new(SETTINGS_SCHEMA)
		DEV_VERSION = self._settings.get_boolean('experimental')

		self.color_btn_l.set_rgba(Gdk.RGBA(red=0.0, green=0.0, blue=0.0, alpha=1.0))
		self.color_btn_r.set_rgba(Gdk.RGBA(red=1.0, green=1.0, blue=1.0, alpha=1.0))
		self.set_palette_setting(None, None)

		# FIXME dimensions ??
		self.pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 1000, 600) # 8 ??? les autres plantent
		self._surface = cairo.ImageSurface(cairo.Format.ARGB32, 1000, 600)
		# self.drawing_area.set_size(1000, 600) # osef

		self.drawing_area.show()

		self.drawing_area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | \
			Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.POINTER_MOTION_MASK)

		self.is_clicked = False
		self.window_has_control = True

		if DEV_VERSION:
			self.tools['select'] = ToolSelect(self)
		self.tools['pencil'] = ToolPencil(self)
		self.tools['eraser'] = ToolEraser(self)
		self.tools['text'] = ToolText(self)
		self.tools['picker'] = ToolPicker(self)
		self.tools['paint'] = ToolPaint(self)
		self.tools['line'] = ToolLine(self)
		self.tools['shape'] = ToolShape(self)
		self.tools['crop'] = ToolCrop(self)
		self.build_tool_rows()
		self.tools_panel.show_all()

		self.tools_buttons['pencil'].set_active(True)
		self.former_tool = self.tools['pencil']

		self.options_popover = None
		self.build_options_popover()
		self.update_size_spinbtn_state(self.active_tool().use_size)
		self.update_size_spinbtn_value(None, None, 10)

		self.build_menu()
		self.add_actions()
		self.connect_signals()

		if self._file_path is not None:
			self.try_load_file(self._file_path)
		else:
			self.init_background()

	def init_background(self):
		w_context = cairo.Context(self._surface)
		r = float(self._settings.get_strv('default-rgba')[0])
		g = float(self._settings.get_strv('default-rgba')[1])
		b = float(self._settings.get_strv('default-rgba')[2])
		a = float(self._settings.get_strv('default-rgba')[3])
		w_context.set_source_rgba(r, g, b, a)
		w_context.paint()

		# equivalent for self.post_modification()
		self.pixbuf = Gdk.pixbuf_get_from_surface(self._surface, 0, 0, \
			self._surface.get_width(), self._surface.get_height())

	# UI BUILDING

	def build_tool_rows(self):
		group = None
		for tool_id in self.tools:
			if group is None:
				group = self.tools[tool_id].row
			else:
				self.tools[tool_id].row.join_group(group)
			self.tools_panel.add(self.tools[tool_id].row)
			self.tools_buttons[tool_id] = self.tools[tool_id].row

	def set_palette_setting(self, a, b):
		color_btn_show_editor = self._settings.get_boolean('direct-color-edit')
		self.color_btn_l.props.show_editor = color_btn_show_editor
		self.color_btn_r.props.show_editor = color_btn_show_editor

	def connect_signals(self):
		self.handlers.append( self.connect('delete-event', self.on_close) )

		self.handlers.append( self.open_btn.connect('clicked', self.action_open) )
		self.handlers.append( self.save_btn.connect('clicked', self.action_save) )
		self.handlers.append( self.undo_btn.connect('clicked', self.on_undo) )
		self.handlers.append( self.redo_btn.connect('clicked', self.on_redo) )

		self.handlers.append( self.menu_btn.connect('toggled', self.on_menu_open) )
		self.handlers.append( self.menu_popover.connect('closed', self.on_menu_popover_closed, self.menu_btn) )

		self.handlers.append( self.color_btn_exc.connect('clicked', self.on_exchange_color) )
		self.handlers.append( self.size_setter.connect('change-value', self.update_size_spinbtn_value) )

		self.handlers.append( self.options_btn.connect('toggled', self.on_options_open) )
		self.handlers.append( self.options_popover.connect('closed', self.on_options_popover_closed, self.options_btn) )

		for id_name in self.tools:
			self.handlers.append( self.tools_buttons[id_name].connect('toggled', self.on_tool_change) )

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

	def add_actions(self):
		action = Gio.SimpleAction.new("import", None)
		action.connect("activate", self.import_png)
		self.add_action(action)

		action = Gio.SimpleAction.new("paste", None)
		action.connect("activate", self.paste)
		self.add_action(action)

		action = Gio.SimpleAction.new("select_all", None)
		action.connect("activate", self.select_all)
		self.add_action(action)

		action = Gio.SimpleAction.new("unselect", None)
		action.connect("activate", self.unselect)
		self.add_action(action)

		action = Gio.SimpleAction.new("properties", None)
		action.connect("activate", self.edit_properties)
		self.add_action(action)

		action = Gio.SimpleAction.new("exp_png", None)
		action.connect("activate", self.export_as_png)
		self.add_action(action)
		action = Gio.SimpleAction.new("exp_jpeg", None)
		action.connect("activate", self.export_as_jpeg)
		self.add_action(action)
		action = Gio.SimpleAction.new("exp_bmp", None)
		action.connect("activate", self.export_as_bmp)
		self.add_action(action)

		action = Gio.SimpleAction.new("close", None)
		action.connect("activate", self.on_close)
		self.add_action(action)

		action = Gio.SimpleAction.new("save", None)
		action.connect("activate", self.action_save)
		self.add_action(action)

		action = Gio.SimpleAction.new("open", None)
		action.connect("activate", self.action_open)
		self.add_action(action)

		action = Gio.SimpleAction.new("undo", None)
		action.connect("activate", self.action_undo)
		self.add_action(action)

		action = Gio.SimpleAction.new("redo", None)
		action.connect("activate", self.action_redo)
		self.add_action(action)

	def update_tools_visibility(self, listbox, gdkrectangle):
		if gdkrectangle.width < 120:
			for label in self.tools:
				self.tools[label].label_widget.set_visible(False)
		else:
			for label in self.tools:
				self.tools[label].label_widget.set_visible(True)

	def update_options_box(self, window, gdkrectangle):
		if gdkrectangle.width < 800:
			self.options_long_box.set_visible(False)
			self.options_short_box.set_visible(True)
		else:
			self.options_short_box.set_visible(False)
			self.options_long_box.set_visible(True)

	def on_menu_open(self, b):
		self.menu_popover.show_all()

	def on_options_open(self, b):
		self.options_popover.show_all()
		b.set_active(False) # illogique mais bon
		self.update_option_label()

	def build_menu(self):
		builder = Gtk.Builder()
		builder.add_from_resource("/com/github/maoschanz/Draw/ui/menus.ui")
		menu = builder.get_object("window-menu")
		self.menu_popover = Gtk.Popover.new_from_model(self.menu_btn, menu)
		self.menu_btn.set_popover(self.menu_popover)

	def on_menu_popover_closed(self, popover, button):
		button.set_active(False)

	def on_exchange_color(self, b):
		left_c = self.color_btn_l.get_rgba()
		self.color_btn_l.set_rgba(self.color_btn_r.get_rgba())
		self.color_btn_r.set_rgba(left_c)

	def update_size_spinbtn_state(self, sensitivity):
		self.size_setter.set_sensitive(sensitivity)

	def update_size_spinbtn_value(self, a, b, c):
		value = int(c)
		self.tool_width = value

	# TOOLS MANAGEMENT

	def build_options_popover(self):
		if self.options_popover is not None:
			self.options_popover.remove(self.options_box)
		self.options_btn.set_sensitive(False)
		self.options_popover = Gtk.Popover()
		self.options_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

		if self.active_tool().use_options:
			self.options_btn.set_sensitive(True)
			self.options_box = self.active_tool().get_options_widget()
		else:
			self.options_btn.set_sensitive(False)

		self.options_popover.add(self.options_box)
		self.options_popover.set_relative_to(self.options_btn)

		self.update_option_label()

	def on_options_popover_closed(self, popover, button): # FIXME jamais appelée ?
		button.set_active(False)
		self.update_option_label()

	def update_option_label(self):
		if self.active_tool().use_options:
			self.options_label.set_label(self.active_tool().get_options_label())
		else:
			self.options_label.set_label(_("No options"))

	def on_tool_change(self, *args):
		self.former_tool.give_back_control()
		self.drawing_area.queue_draw()
		self.former_tool = self.active_tool()
		self.build_options_popover()
		self.update_option_label()
		self.update_size_spinbtn_state(self.active_tool().use_size)

	def active_tool(self):
		for tool_id in self.tools:
			if self.tools_buttons[tool_id].get_active():
				return self.tools[tool_id]
		return self.tools['pencil']

	# FILE MANAGEMENT

	def action_save(self, *args):
		if self._file_path is None:
			self._file_path = self.invoke_file_chooser()
			self.header_bar.set_subtitle(self._file_path)

		if self._file_path is not None:
			(pb_format, width, height) = GdkPixbuf.Pixbuf.get_file_info(self._file_path)

			self.pixbuf = Gdk.pixbuf_get_from_surface(self._surface, 0, 0, \
				self._surface.get_width(), self._surface.get_height())
			self.pixbuf.savev(self._file_path, pb_format.get_name(), [None], [])

			self._is_saved = True

	def action_open(self, *args):
		# Asking what to do before overwriting the picture in the window
		if not self.confirm_save_modifs():
			return

		file_chooser = Gtk.FileChooserNative.new(_("Open a picture"), self,
			Gtk.FileChooserAction.OPEN,
			_("Open"),
			_("Cancel"))
		onlyPictures = Gtk.FileFilter()
		onlyPictures.set_name(_("Pictures"))
		onlyPictures.add_mime_type('image/png')
		onlyPictures.add_mime_type('image/jpeg')
		onlyPictures.add_mime_type('image/bmp')
		file_chooser.add_filter(onlyPictures)
		response = file_chooser.run()
		if response == Gtk.ResponseType.ACCEPT:
			self.try_load_file(file_chooser.get_filename())
		file_chooser.destroy()

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
			dialog = Gtk.MessageDialog(modal=True, title=title_label, parent=self)
			dialog.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
			dialog.add_button(_("Edit it anyway"), Gtk.ResponseType.NO)
			dialog.add_button(_("Scale it"), Gtk.ResponseType.APPLY)
			dialog.add_button(_("Crop it"), Gtk.ResponseType.YES)
			dialog.get_message_area().add(Gtk.Label(label=_("What would you prefer?")))
			dialog.show_all()
			result = dialog.run()

			if result == Gtk.ResponseType.NO: # Edit it anyway
				self._file_path = fn
				self.pixbuf = GdkPixbuf.Pixbuf.new_from_file(fn)
				self.initial_save()
			elif result == Gtk.ResponseType.APPLY: # Resize it
				self._file_path = fn
				self.pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(fn, w, h, True)
				self.initial_save()
			elif result == Gtk.ResponseType.YES: # Crop it
				crop_dialog = DrawCropDialog(self, fn)
			else: # Cancel
				pass
			dialog.destroy()
		else:
			self._file_path = fn
			self.pixbuf = GdkPixbuf.Pixbuf.new_from_file(fn)
			self.initial_save()

	def initial_save(self):
		self.header_bar.set_subtitle(self._file_path)
		self._is_saved = True
		self.pre_modification()

	def confirm_save_modifs(self):
		if not self._is_saved:
			if self._file_path is None:
				title_label = _("Untitled") + '.png'
			else:
				title_label = self._file_path.split('/')[-1]
			dialog = Gtk.MessageDialog(modal=True, title=title_label, parent=self)
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

	def on_close(self, *args):
		if self.confirm_save_modifs():
			return False
		else:
			return True

	# HISTORY MANAGEMENT

	def action_undo(self, *args):
		if len(self.undo_history) == 0:
			return
		else:
			self.on_undo(None)

	def action_redo(self, *args):
		if len(self.redo_history) == 0:
			return
		else:
			self.on_redo(None)

	def on_undo(self, b):
		self.redo_history.append(self.pixbuf.copy())
		self.pixbuf = self.undo_history.pop()
		self.pre_modification()

		self.drawing_area.queue_draw()
		self.update_history_sensitivity()

	def on_redo(self, b):
		self.undo_history.append(self.pixbuf.copy())
		self.pixbuf = self.redo_history.pop()
		self.pre_modification()

		self.drawing_area.queue_draw()
		self.update_history_sensitivity()

	def update_history_sensitivity(self):
		if len(self.undo_history) == 0:
			self.undo_btn.set_sensitive(False)
		else:
			self.undo_btn.set_sensitive(True)

		if len(self.redo_history) == 0:
			self.redo_btn.set_sensitive(False)
		else:
			self.redo_btn.set_sensitive(True)

	def pre_modification(self):
		# on restaure depuis le pixbuf la surface enregistrée précédemment
		self._surface = Gdk.cairo_surface_create_from_pixbuf(self.pixbuf, 0, None)
		# return self._surface

	def post_modification(self):
		self.undo_history.append(self.pixbuf.copy())
		self.redo_history = []
		self.update_history_sensitivity()

		# on enregistre la surface dans le pixbuf
		self.pixbuf = Gdk.pixbuf_get_from_surface(self._surface, 0, 0, \
			self._surface.get_width(), self._surface.get_height())

	# DRAWING OPERATIONS

	def on_draw(self, area, cairo_context):
		# Ça marche mais je ne sais pas si avoir une surface ne serait pas mieux.
		# Gdk.cairo_set_source_pixbuf(cairo_context, self.pixbuf, 0, 0)

		# Ça marche aussi mais c'est moins idéal complexitivement.
		# surface = Gdk.cairo_surface_create_from_pixbuf(self.pixbuf, 0, None)
		cairo_context.set_source_surface(self._surface, 0, 0)

		cairo_context.paint()

	def on_configure(self, area, cairo_context):
		print("ceci est appelé quand ça dimensionne la zone")

	def on_key_on_area(self, area, event):
		print("key") # TODO les touches sont des constantes Gdk

		self.active_tool().on_key_on_area(area, event, self._surface)

		self.drawing_area.queue_draw()

	def on_motion_on_area(self, area, event):
		if (not self.is_clicked):
			return
		self.active_tool().on_motion_on_area(area, event, self._surface)
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

		self.active_tool().on_press_on_area(area, event, self._surface, \
			self.size_setter.get_value(), self.color_btn_l.get_rgba(), self.color_btn_r.get_rgba())

	def on_release_on_area(self, area, event):
		if not self.is_clicked:
			return
		self.is_clicked = False

		self.active_tool().on_release_on_area(area, event, self._surface)
		self.window_has_control = self.active_tool().window_can_take_back_control

		self.drawing_area.queue_draw()

		if self.window_has_control:
			print('release où la fenêtre a récupéré le contrôle')
			self.post_modification()

	# OTHER UNIMPLEMENTED OPERATIONS TODO

	def import_png(self, *args):
		print("import")

	def paste(self, *args):
		print("paste")

	def select_all(self, *args):
		print("select_all")

	def unselect(self, *args):
		print("unselect")

	def edit_properties(self, *args):
		DrawPropertiesDialog(self)

###########################

	def invoke_file_chooser(self):
		file_path = None
		file_chooser = Gtk.FileChooserNative.new(_("Save as"), self,
			Gtk.FileChooserAction.SAVE,
			_("Save"),
			_("Cancel"))
		onlyPictures = Gtk.FileFilter()
		onlyPictures.set_name(_("Pictures"))
		onlyPictures.add_mime_type('image/png')
		onlyPictures.add_mime_type('image/jpeg')
		onlyPictures.add_mime_type('image/bmp')
		file_chooser.add_filter(onlyPictures)
		response = file_chooser.run()
		if response == Gtk.ResponseType.ACCEPT:
			file_path = file_chooser.get_filename()
		file_chooser.destroy()
		return file_path

	def export_as_png(self, *args):
		file_path = self.invoke_file_chooser()
		self.post_modification()
		self.pixbuf.savev(file_path, "png", [None], [])

	def export_as_jpeg(self, *args):
		file_path = self.invoke_file_chooser()
		self.post_modification()
		self.pixbuf.savev(file_path, "jpeg", [None], [])

	def export_as_bmp(self, *args):
		file_path = self.invoke_file_chooser()
		self.post_modification()
		self.pixbuf.savev(file_path, "bmp", [None], [])

	def resize_surface(self, x, y, width, height):
		x = int(x)
		y = int(y)
		width = int(width)
		height = int(height)

		# The GdkPixbuf.Pixbuf.copy_area method works only when expanding the size
		max_width = max(width, self._surface.get_width())
		max_height = max(height, self._surface.get_height())
		new_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, max_width, max_height)
		self.pixbuf.copy_area(0, 0, self._surface.get_width(), self._surface.get_height(), new_pixbuf, 0, 0)
		self.pixbuf = new_pixbuf

		# The cairo.Surface.map_to_image method works only when reducing the size
		self._surface = Gdk.cairo_surface_create_from_pixbuf(self.pixbuf, 0, None)
		self._surface = self._surface.map_to_image(cairo.RectangleInt(x, y, width, height))
		self.pixbuf = Gdk.pixbuf_get_from_surface(self._surface, 0, 0, \
			self._surface.get_width(), self._surface.get_height())

		self.drawing_area.set_size(width, height)

		if x != 0 or y != 0:
			self.resize_surface(0, 0, width, height)
