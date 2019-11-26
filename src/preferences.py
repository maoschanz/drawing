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
from .utilities import utilities_add_unit_to_spinbtn

SETTINGS_SCHEMA = 'com.github.maoschanz.drawing'

@Gtk.Template(resource_path='/com/github/maoschanz/drawing/ui/preferences.ui')
class DrawingPrefsWindow(Gtk.Window):
	__gtype_name__ = 'DrawingPrefsWindow'

	content_area = Gtk.Template.Child()
	stack_switcher = Gtk.Template.Child()

	page_images = Gtk.Template.Child()
	page_tools = Gtk.Template.Child()
	page_advanced = Gtk.Template.Child()

	adj_width = Gtk.Template.Child()
	adj_height = Gtk.Template.Child()
	adj_preview = Gtk.Template.Child()

	_settings = Gio.Settings.new('com.github.maoschanz.drawing')

	def __init__(self, is_beta, wants_csd, **kwargs):
		super().__init__(**kwargs)
		if wants_csd:
			header_bar = Gtk.HeaderBar(visible=True, title=_("Preferences"), \
			                                             show_close_button=True)
			self.set_titlebar(header_bar)
			self.content_area.remove(self.stack_switcher)
			header_bar.set_custom_title(self.stack_switcher)
		else:
			self.stack_switcher.set_margin_top(10)

		########################################################################
		# Build the "images" page ##############################################
		pass

		w = self.new_section_title(_("New images"), False)
		self.page_images.add(w)

		w = self.row_from_adj(_("Default width"), 'default-width', self.adj_width)
		self.page_images.add(w)

		w = self.row_from_adj(_("Default height"), 'default-height', self.adj_height)
		self.page_images.add(w)

		bg_color_btn = Gtk.ColorButton(use_alpha=True)
		background_rgba = self._settings.get_strv('background-rgba')
		r = float(background_rgba[0])
		g = float(background_rgba[1])
		b = float(background_rgba[2])
		a = float(background_rgba[3])
		color = Gdk.RGBA(red=r, green=g, blue=b, alpha=a)
		bg_color_btn.set_rgba(color)
		bg_color_btn.connect('color-set', self.on_background_changed)
		w = self.row_from_widget(_("Default background"), bg_color_btn, False)
		self.page_images.add(w)

		w = self.new_section_title(_("Images saving"), True)
		self.page_images.add(w)

		w = self.row_for_help_label(_("JPEG and BMP images can't handle " + \
		     "transparency. If you save your images in these formats, what " + \
		                       "do want to use to replace transparent pixels?"))
		self.page_images.add(w)

		labels = [_("White"), _("Black"), _("Checkboard"), _("Ask before saving")]
		ids = ['white', 'black', 'checkboard', 'ask']
		w = self.new_radio_flowbox('replace-alpha', labels, ids)
		self.page_images.add(w)

		w = self.new_section_title(_("Zoom"), True)
		self.page_images.add(w)

		scroll_combobox = Gtk.ComboBoxText()
		scroll_combobox.append('ctrl', _("Ctrl + Scroll"))
		scroll_combobox.append('scroll', _("Scroll"))
		scroll_combobox.set_active_id(self._settings.get_string('zoom-behavior'))
		scroll_combobox.connect('changed', self.on_combo_changed, 'zoom-behavior')
		w = self.row_from_widget(_("Action to zoom"), scroll_combobox, False)
		self.page_images.add(w)

		w = self.row_from_bool(_("Automatic zoom level"), 'auto-zoom')
		self.page_images.add(w)

		########################################################################
		# Build the "tools" page ###############################################
		pass

		w = self.new_section_title(_("Appearance"), False)
		self.page_tools.add(w)

		w = self.row_from_bool(_("Show tools names"), 'show-labels')
		self.page_tools.add(w)

		w = self.row_from_bool(_("Use big icons"), 'big-icons')
		self.page_tools.add(w)

		w = self.new_section_title(_("Additional tools"), True)
		self.page_tools.add(w)

		w = self.row_for_help_label(_("These tools are not as reliable and " + \
		   "useful as they should be, so they are not all enabled by default."))
		self.page_tools.add(w)

		flowbox = Gtk.FlowBox(visible=True, selection_mode=Gtk.SelectionMode.NONE)
		self.page_tools.add(flowbox)
		w = self.build_check_btn(_("Free selection"), 'free_select', 'disabled-tools')
		flowbox.add(w)
		w = self.build_check_btn(_("Color selection"), 'color_select', 'disabled-tools')
		flowbox.add(w)
		w = self.build_check_btn(_("Color Picker"), 'picker', 'disabled-tools')
		flowbox.add(w)
		w = self.build_check_btn(_("Paint"), 'paint', 'disabled-tools')
		flowbox.add(w)

		########################################################################
		# Build the "advanced" page ############################################
		pass

		w = self.new_section_title(_("Advanced options"), False)
		self.page_advanced.add(w)

		w = self.row_from_adj(_("Preview size"), 'preview-size', self.adj_preview)
		self.page_advanced.add(w)

		if not is_beta:
			self._settings.set_boolean('devel-only', False)
		w = self.row_from_bool(_("Development features"), 'devel-only')
		self.page_advanced.add(w)
		if not is_beta:
			w.set_visible(False)

		w = self.new_section_title(_("Layout"), True)
		self.page_advanced.add(w)

		w = self.row_for_help_label(_("The recommended value is \"Automatic\"."))
		self.page_advanced.add(w)

		labels = [_("Automatic"), _("Compact"), "elementary OS", \
		         _("Legacy"), _("Legacy (symbolic icons)"), _("Menubar only"), \
		                  _("Toolbar only"), _("Toolbar only (symbolic icons)")]
		ids = ['auto', 'csd', 'csd-eos', 'ssd', 'ssd-symbolic', 'ssd-menubar', \
		                                  'ssd-toolbar', 'ssd-toolbar-symbolic']
		w = self.new_radio_flowbox('decorations', labels, ids)
		self.page_advanced.add(w)

	############################################################################
	# Widgets building methods #################################################

	def new_section_title(self, label_text, with_margin):
		label = Gtk.Label(halign=Gtk.Align.START, use_markup=True, \
		                                    label=('<b>' + label_text + '</b>'))
		if with_margin:
			label.set_margin_top(12)
		label.set_visible(True)
		return label

	def new_radio_flowbox(self, setting_key, labels, ids):
		flowbox = Gtk.FlowBox(visible=True, selection_mode=Gtk.SelectionMode.NONE)
		self._radio_are_active = False
		w0 = None
		for i in range(len(labels)):
			w0 = self.build_radio_btn(labels[i], ids[i], setting_key, w0)
			flowbox.add(w0)
		self._radio_are_active = True
		return flowbox

	def row_for_help_label(self, label_text):
		help_btn = Gtk.Button.new_from_icon_name('help-faq-symbolic', \
		                                                    Gtk.IconSize.BUTTON)
		help_btn.set_valign(Gtk.Align.CENTER)
		help_btn.set_relief(Gtk.ReliefStyle.NONE)
		help_btn.connect('clicked', self.get_application().on_help_prefs)
		return self.row_from_widget(label_text, help_btn, True)

	def row_from_widget(self, label_text, widget, wrap_and_dim):
		label = Gtk.Label(label=label_text)
		box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
		box.pack_start(label, expand=False, fill=False, padding=0)
		if widget is not None:
			box.pack_end(widget, expand=False, fill=False, padding=0)
		if wrap_and_dim:
			label.set_line_wrap(True)
			label.get_style_context().add_class('dim-label')
		box.show_all()
		return box

	def row_from_bool(self, label_text, key):
		switch = Gtk.Switch()
		switch.set_active(self._settings.get_boolean(key))
		switch.connect('notify::active', self.on_bool_changed, key)
		return self.row_from_widget(label_text, switch, False)

	def row_from_adj(self, label_text, key, adj):
		spinbtn = Gtk.SpinButton(adjustment=adj)
		spinbtn.set_value(self._settings.get_int(key))
		utilities_add_unit_to_spinbtn(spinbtn, 4, 'px')
		spinbtn.connect('value-changed', self.on_adj_changed, key)
		return self.row_from_widget(label_text, spinbtn, False)

	def build_radio_btn(self, label, btn_id, key, group):
		btn = Gtk.RadioButton(label=label, visible=True, group=group)
		active_id = self._settings.get_string(key)
		btn.set_active(btn_id == active_id)
		btn.connect('toggled', self.on_radio_btn_changed, key, btn_id)
		return btn

	def build_check_btn(self, label, row_id, key):
		btn = Gtk.CheckButton(label=label, visible=True)
		array_of_strings = self._settings.get_strv(key)
		btn.set_active(row_id not in array_of_strings)
		btn.connect('toggled', self.on_check_btn_changed, key, row_id)
		return btn

	############################################################################

	def on_bool_changed(self, switch, state, key):
		self._settings.set_boolean(key, switch.get_active())

	def on_adj_changed(self, spinbtn, key):
		self._settings.set_int(key, spinbtn.get_value_as_int())

	def on_background_changed(self, color_btn):
		c = color_btn.get_rgba()
		color_array = [str(c.red), str(c.green), str(c.blue), str(c.alpha)]
		self._settings.set_strv('background-rgba', color_array)

	def on_combo_changed(self, combobox, key):
		self._settings.set_string(key, combobox.get_active_id())

	def on_check_btn_changed(self, checkbtn, key, btn_id):
		array_of_strings = self._settings.get_strv(key)
		if checkbtn.get_active():
			array_of_strings.remove(btn_id)
		else:
			array_of_strings.append(btn_id)
		self._settings.set_strv(key, array_of_strings)

	def on_radio_btn_changed(self, radiobtn, key, btn_id):
		if self._radio_are_active:
			self._settings.set_string(key, btn_id)

	############################################################################
################################################################################

