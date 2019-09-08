# preferences.py
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Gtk, Gio, GLib, Gdk
from .gi_composites import GtkTemplate

from .utilities import utilities_add_px_to_spinbutton

SETTINGS_SCHEMA = 'com.github.maoschanz.drawing'

@GtkTemplate(ui='/com/github/maoschanz/drawing/ui/preferences.ui')
class DrawingPrefsWindow(Gtk.Window):
	__gtype_name__ = 'DrawingPrefsWindow'

	content_area = GtkTemplate.Child()
	stack_switcher = GtkTemplate.Child()

	page_images = GtkTemplate.Child()
	page_tools = GtkTemplate.Child()
	page_advanced = GtkTemplate.Child()

	adj_width = GtkTemplate.Child()
	adj_height = GtkTemplate.Child()
	adj_preview = GtkTemplate.Child()

	_settings = Gio.Settings.new('com.github.maoschanz.drawing')

	def __init__(self, is_beta, wants_csd, **kwargs):
		super().__init__(**kwargs)
		self.init_template()
		if wants_csd:
			header_bar = Gtk.HeaderBar(visible=True, title=_("Preferences"), \
			                                             show_close_button=True)
			self.set_titlebar(header_bar)
			self.content_area.remove(self.stack_switcher)
			header_bar.set_custom_title(self.stack_switcher)

		########################################################################
		# Build the "images" page ##############################################

		pass
		w = self.row_from_label(_("New images"), False)
		self.page_images.add(w)

		w = self.row_from_adj(_("Default width"), 'default-width', self.adj_width)
		self.page_images.add(w)

		w = self.row_from_adj(_("Default height"), 'default-height', self.adj_height)
		self.page_images.add(w)

		background_color_btn = Gtk.ColorButton(use_alpha=True)
		background_rgba = self._settings.get_strv('background-rgba')
		r = float(background_rgba[0])
		g = float(background_rgba[1])
		b = float(background_rgba[2])
		a = float(background_rgba[3])
		color = Gdk.RGBA(red=r, green=g, blue=b, alpha=a)
		background_color_btn.set_rgba(color)
		background_color_btn.connect('color-set', self.on_background_changed)
		w = self.row_from_widget(_("Default background"), background_color_btn)
		self.page_images.add(w)

		w = self.row_from_label(_("Opened images"), True)  # TODO move this section to "advanced"
		self.page_images.add(w)

		w = self.row_from_bool(_("Always add transparency"), 'add-alpha')
		self.page_images.add(w)

		########################################################################
		# Build the "tools" page ###############################################

		pass
		w = self.row_from_bool(_("Show tools names"), 'show-labels')
		self.page_tools.add(w)

		w = self.row_from_bool(_("Use big icons"), 'big-icons')
		self.page_tools.add(w)

		########################################################################
		# Build the "advanced" page ############################################

		pass
		w = self.row_from_label(_("Advanced options"), False)
		self.page_advanced.add(w)

		w = self.row_from_adj(_("Preview size"), 'preview-size', self.adj_preview)
		self.page_advanced.add(w)

		layout_combobox = Gtk.ComboBoxText()
		layout_combobox.append('auto', _("Automatic"))
		layout_combobox.append('csd', _("Compact"))
		layout_combobox.append('csd-eos', 'elementary OS')
		# "Legacy" is about the window layout, it means menubar+toolbar, you can
		# translate it like if it was "Traditional"
		layout_combobox.append('ssd', _("Legacy"))
		# SHORT STRING PLEASE
		# "Legacy" is about the window layout, it means menubar+toolbar, you can
		# translate it like if it was "Traditional". "symbolic" means the icons
		# are in black or white.
		layout_combobox.append('ssd-symbolic', _("Legacy (symbolic)"))
		layout_combobox.append('ssd-menubar', _("Menubar only"))
		layout_combobox.append('ssd-toolbar', _("Toolbar only"))
		# SHORT STRING PLEASE
		# "symbolic" means the icons are in black or white.
		layout_combobox.append('ssd-toolbar-symbolic', _("Toolbar (symbolic)"))
		if is_beta and self._settings.get_boolean('devel-only'):
			layout_combobox.append('everything', "Everything (testing only)")
		layout_combobox.set_active_id(self._settings.get_string('decorations'))
		layout_combobox.connect('changed', self.on_combo_changed, 'decorations')
		w = self.row_from_widget(_("Layout"), layout_combobox)
		self.page_advanced.add(w)

		if not is_beta:
			self._settings.set_boolean('devel-only', False)
		w = self.row_from_bool(_("Development features"), 'devel-only')
		self.page_advanced.add(w)
		if not is_beta:
			w.set_visible(False)

	############################################################################

	def row_from_label(self, label_text, with_margin):
		label = Gtk.Label(halign=Gtk.Align.START, use_markup=True, \
		                                    label=('<b>' + label_text + '</b>'))
		if with_margin:
			label.set_margin_top(12)
		label.set_visible(True)
		return label

	def row_from_widget(self, label_text, widget):
		label = Gtk.Label(label=label_text)
		box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
		box.pack_start(label, expand=False, fill=False, padding=0)
		box.pack_end(widget, expand=False, fill=False, padding=0)
		box.show_all()
		return box

	def row_for_AoS(self, label, row_id, key):
		btn = Gtk.CheckButton(label=label, visible=True)
		array_of_strings = self._settings.get_strv(key)
		btn.set_active(row_id not in array_of_strings)
		btn.connect('toggled', self.on_aos_checkbtn_changed, key, row_id)
		return btn

	def row_from_bool(self, label_text, key):
		switch = Gtk.Switch()
		switch.set_active(self._settings.get_boolean(key))
		switch.connect('notify::active', self.on_bool_changed, key)
		return self.row_from_widget(label_text, switch)

	def on_bool_changed(self, switch, state, key):
		self._settings.set_boolean(key, switch.get_active())

	def row_from_adj(self, label_text, key, adj):
		spinbtn = Gtk.SpinButton(adjustment=adj)
		spinbtn.set_value(self._settings.get_int(key))
		utilities_add_px_to_spinbutton(spinbtn, 4, 'px')
		spinbtn.connect('value-changed', self.on_adj_changed, key)
		return self.row_from_widget(label_text, spinbtn)

	def on_adj_changed(self, spinbtn, key):
		self._settings.set_int(key, spinbtn.get_value_as_int())

	def on_background_changed(self, color_btn):
		c = color_btn.get_rgba()
		color_array = [str(c.red), str(c.green), str(c.blue), str(c.alpha)]
		self._settings.set_strv('background-rgba', color_array)

	def on_combo_changed(self, combobox, key):
		self._settings.set_string(key, combobox.get_active_id())

	def on_aos_checkbtn_changed(self, checkbtn, key, row_id):
		array_of_strings = self._settings.get_strv(key)
		if checkbtn.get_active():
			array_of_strings.remove(row_id)
		else:
			array_of_strings.append(row_id)
		self._settings.set_strv(key, array_of_strings)

	############################################################################
################################################################################

