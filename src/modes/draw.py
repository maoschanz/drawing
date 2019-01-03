# draw.py
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

from gi.repository import Gtk, Gdk, Gio, GLib

from .modes import ModeTemplate

from .color_popover import DrawingColorPopover

class ModeDraw(ModeTemplate):
	__gtype_name__ = 'ModeDraw'

	def __init__(self, window):
		super().__init__(window)

		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/Drawing/modes/ui/draw.ui')
		self.bottom_panel = builder.get_object('bottom-panel')

		self.color_menu_btn_l = builder.get_object('color_menu_btn_l')
		self.color_menu_btn_r = builder.get_object('color_menu_btn_r')
		self.l_btn_image = builder.get_object('l_btn_image')
		self.r_btn_image = builder.get_object('r_btn_image')
		self.build_color_buttons()

		self.tool_width = 10
		self.size_setter = builder.get_object('size_setter')
		self.size_setter.connect('change-value', self.update_size_spinbtn_value)

		self.options_btn = builder.get_object('options_btn')
		self.options_label = builder.get_object('options_label')
		self.options_long_box = builder.get_object('options_long_box')
		self.options_short_box = builder.get_object('options_short_box')
		self.options_btn.connect('toggled', self.update_option_label)

		self.tool_info_label = builder.get_object('tool_info_label') # TODO

		self.minimap_area = None
		self.minimap_btn = builder.get_object('minimap_btn')
		self.minimap_icon = builder.get_object('minimap_icon')
		self.minimap_label = builder.get_object('minimap_label')
		self.build_minimap()

	def get_panel(self):
		return self.bottom_panel

	def adapt_to_window_size(self):
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

	def on_tool_changed(self):
		self.build_options_menu()
		self.update_size_spinbtn_state()

	def on_motion_on_area(self, area, event, surface):
		self.window.active_tool().on_motion_on_area(area, event, surface)

	def on_press_on_area(self, area, event, surface):
		self.tool_width = int(self.size_setter.get_value())
		if event.button is 2:
			self.action_exchange_color()
			return
		self.window.active_tool().on_press_on_area(area, event, surface, \
			self.size_setter.get_value(), \
			self.color_popover_l.color_widget.get_rgba(), \
			self.color_popover_r.color_widget.get_rgba() )

	def on_release_on_area(self, area, event, surface):
		self.window.active_tool().on_release_on_area(area, event, surface)

###############################

	def build_color_buttons(self):
		white = Gdk.RGBA(red=1.0, green=1.0, blue=1.0, alpha=1.0)
		black = Gdk.RGBA(red=0.0, green=0.0, blue=0.0, alpha=1.0)
		self.color_popover_r = DrawingColorPopover(self.color_menu_btn_r, self.r_btn_image, white)
		self.color_popover_l = DrawingColorPopover(self.color_menu_btn_l, self.l_btn_image, black)

	def action_use_editor(self, *args):
		self.window._settings.set_boolean('direct-color-edit', not args[0].get_state())
		args[0].set_state(GLib.Variant.new_boolean(not args[0].get_state()))
		self.set_palette_setting()

	def set_palette_setting(self, *args):
		show_editor = self.window._settings.get_boolean('direct-color-edit')
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

############################

	def update_size_spinbtn_state(self):
		sensitivity = self.window.active_tool().use_size
		self.size_setter.set_sensitive(sensitivity)

	def update_size_spinbtn_value(self, *args):
		self.tool_width = int(args[2])

############################

	def build_options_menu(self):
		widget = self.window.active_tool().get_options_widget()
		model = self.window.active_tool().get_options_model()
		tools_menu = self.window.app.get_menubar().get_item_link(5, Gio.MENU_LINK_SUBMENU)
		section = tools_menu.get_item_link(0, Gio.MENU_LINK_SECTION)
		if model is None:
			section.get_item_link(0, Gio.MENU_LINK_SUBMENU).remove_all()
		else:
			section.remove_all()
			section.append_submenu(_("Tool options"), model)
		if widget is not None:
			self.options_btn.set_popover(widget)
		elif model is not None:
			self.options_btn.set_menu_model(model)
		else:
			self.options_btn.set_popover(None)
		self.update_option_label()

	def update_option_label(self, *args):
		self.options_label.set_label(self.window.active_tool().get_options_label())

############################

	def action_toggle_preview(self, *args):
		self.minimap_btn.set_active(not self.minimap_btn.get_active())

	def action_smaller_preview(self, *args):
		size = max(200, self._settings.get_int('preview-size') - 40)
		self.window._settings.set_int('preview-size', size)
		self.window._pixbuf_manager.preview_size = size
		self.window._pixbuf_manager.update_minimap()

	def action_bigger_preview(self, *args):
		size = self._settings.get_int('preview-size') + 40
		self.window._settings.set_int('preview-size', size)
		self.window._pixbuf_manager.preview_size = size
		self.window._pixbuf_manager.update_minimap()

	def build_minimap(self):
		builder = Gtk.Builder()
		builder.add_from_resource('/com/github/maoschanz/Drawing/ui/minimap.ui')
		box = builder.get_object('minimap_box')
		self.minimap_area = builder.get_object('minimap_area')
		self.minimap_area.set_size(200, 200)
		minimap_popover = Gtk.Popover()
		minimap_popover.add(box)
		self.minimap_btn.set_popover(minimap_popover)

		self.minimap_area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | \
			Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.POINTER_MOTION_MASK)

		self.minimap_area.connect('draw', self.on_minimap_draw)
		# self.minimap_area.connect('motion-notify-event', self.on_minimap_motion)
		self.minimap_area.connect('button-press-event', self.on_minimap_press)
		self.minimap_area.connect('button-release-event', self.on_minimap_release)

	def on_minimap_draw(self, area, cairo_context):
		cairo_context.set_source_surface(self.window._pixbuf_manager.mini_surface, 0, 0)
		cairo_context.paint()

	def on_minimap_press(self, area, event):
		self.window._pixbuf_manager.on_minimap_press(event.x, event.y)

	def on_minimap_release(self, area, event):
		self.window._pixbuf_manager.on_minimap_release(event.x, event.y)


