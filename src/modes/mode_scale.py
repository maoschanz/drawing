# scale.py
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

from gi.repository import Gtk, Gdk, Gio, GLib, GdkPixbuf

from .modes import ModeTemplate

class ModeScale(ModeTemplate):
	__gtype_name__ = 'ModeScale'

	def __init__(self, window):
		super().__init__(window)
		self.keep_proportions = True
		self.x_press = 0
		self.y_press = 0

		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/Drawing/modes/ui/mode_scale.ui')
		self.bottom_panel = builder.get_object('bottom-panel')
		self.centered_box = builder.get_object('centered_box')
		self.cancel_btn = builder.get_object('cancel_btn')
		self.apply_btn = builder.get_object('apply_btn')

		self.height_btn = builder.get_object('height_btn')
		self.width_btn = builder.get_object('width_btn')
		self.width_btn.connect('value-changed', self.on_width_changed)
		self.height_btn.connect('value-changed', self.on_height_changed)

		self.add_mode_action_boolean('keep_proportions', True, self.set_keep_proportions)
		self.needed_width_for_long = 0

	def get_panel(self):
		return self.bottom_panel

	def get_edition_status(self):
		if self.scale_selection:
			return _("Scaling the selection")
		else:
			return _("Scaling the canvas")

	def set_keep_proportions(self, *args):
		args[0].set_state(GLib.Variant.new_boolean(not args[0].get_state()))
		self.keep_proportions = args[0].get_state()
		if self.keep_proportions:
			self.proportion = self.get_width()/self.get_height()

	def on_apply_mode(self):
		w = self.get_width()
		h = self.get_height()
		if self.scale_selection:
			self.window.active_tool().scale_pixbuf_to(w, h)
		else:
			self.window.scale_pixbuf_to(w, h)

	def on_draw(self, area, cairo_context, main_x, main_y):
		if self.scale_selection:
			self.window.use_stable_pixbuf()
			self.window.active_tool().delete_temp()
			selection_x = self.window.active_tool().selection_x
			selection_y = self.window.active_tool().selection_y
			self.window.show_pixbuf_content_at(self.window.temporary_pixbuf, selection_x, selection_y)
			super().on_draw(area, cairo_context, main_x, main_y)
		else:
			Gdk.cairo_set_source_pixbuf(cairo_context, self.window.temporary_pixbuf, -1 * main_x, -1 * main_y)
			cairo_context.paint()

	def update_temp_pixbuf(self):
		w = self.get_width()
		h = self.get_height()
		if self.scale_selection:
			self.window.temporary_pixbuf = self.window.active_tool().selection_pixbuf.scale_simple( \
				w, h, GdkPixbuf.InterpType.TILES)
		else:
			self.window.temporary_pixbuf = self.window.main_pixbuf.scale_simple(w, h, GdkPixbuf.InterpType.TILES)

	def on_mode_selected(self, *args):
		self.scale_selection = args[0]
		if self.scale_selection:
			w = self.window.active_tool().selection_pixbuf.get_width()
			h = self.window.active_tool().selection_pixbuf.get_height()
		else:
			w = self.window.get_pixbuf_width()
			h = self.window.get_pixbuf_height()
		self.proportion = w/h
		self.width_btn.set_value(w)
		self.height_btn.set_value(h)
		self.set_action_sensitivity('active_tool', False)

	def on_width_changed(self, *args):
		if self.keep_proportions:
			if self.proportion != self.get_width()/self.get_height():
				self.height_btn.set_value(self.get_width()/self.proportion)
		self.update_temp_pixbuf()
		self.non_destructive_show_modif()

	def on_height_changed(self, *args):
		if self.keep_proportions:
			if self.proportion != self.get_width()/self.get_height():
				self.width_btn.set_value(self.get_height()*self.proportion)
		self.update_temp_pixbuf()
		self.non_destructive_show_modif()

	def get_width(self):
		return self.width_btn.get_value_as_int()

	def get_height(self):
		return self.height_btn.get_value_as_int()

	def on_motion_on_area(self, area, event, surface, event_x, event_y):
		delta_x = event.x - self.x_press
		self.width_btn.set_value(self.width_btn.get_value() + delta_x)
		if not self.keep_proportions:
			delta_y = event.y - self.y_press
			self.height_btn.set_value(self.height_btn.get_value() + delta_y)
		self.x_press = event.x
		self.y_press = event.y

	def on_press_on_area(self, area, event, surface, event_x, event_y):
		self.x_press = event.x
		self.y_press = event.y

	def adapt_to_window_size(self):
		available_width = self.window.bottom_panel.get_allocated_width()
		if self.centered_box.get_orientation() == Gtk.Orientation.HORIZONTAL:
			self.needed_width_for_long = self.centered_box.get_preferred_width()[0] + \
				self.cancel_btn.get_allocated_width() + \
				self.apply_btn.get_allocated_width()
		if self.needed_width_for_long > 0.8 * available_width:
			self.centered_box.set_orientation(Gtk.Orientation.VERTICAL)
		else:
			self.centered_box.set_orientation(Gtk.Orientation.HORIZONTAL)
