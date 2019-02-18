# tool_scale.py # XXX
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

from gi.repository import Gtk, Gdk, GdkPixbuf

from .tools import ToolTemplate

class ToolScale(ToolTemplate):
	__gtype_name__ = 'ToolScale'

	implements_panel = True

	def __init__(self, window):
		super().__init__('scale', _("Scale"), 'tool-scale-symbolic', window, True)
		self.need_temp_pixbuf = True

		self.keep_proportions = True
		self.x_press = 0
		self.y_press = 0

		self.add_tool_action_simple('scale_apply', self.on_apply)

		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/Drawing/tools/ui/tool_scale.ui')
		self.bottom_panel = builder.get_object('bottom-panel')
		self.centered_box = builder.get_object('centered_box')
		self.cancel_btn = builder.get_object('cancel_btn')
		self.apply_btn = builder.get_object('apply_btn')

		self.height_btn = builder.get_object('height_btn')
		self.width_btn = builder.get_object('width_btn')
		self.width_btn.connect('value-changed', self.on_width_changed)
		self.height_btn.connect('value-changed', self.on_height_changed)
		builder.get_object('proportions_btn').connect('toggled', self.set_keep_proportions)

		self.add_tool_action_boolean('keep_proportions', True)
		self.needed_width_for_long = 0

		self.window.bottom_panel_box.add(self.bottom_panel)

	def get_panel(self):
		return self.bottom_panel

	def get_edition_status(self):
		if self.scale_selection:
			return _("Scaling the selection")
		else:
			return _("Scaling the canvas")

	def set_keep_proportions(self, *args):
		self.keep_proportions = args[0].get_active()
		if self.keep_proportions:
			self.proportion = self.get_width()/self.get_height()

	def on_apply(self, *args):
		w = self.get_width()
		h = self.get_height()
		if self.scale_selection:
			self.get_image().selection_pixbuf = self.get_selection_pixbuf().scale_simple( \
				w, h, GdkPixbuf.InterpType.TILES)
			self.window.get_selection_tool().on_confirm_hijacked_modif()
		else:
			pb = self.get_main_pixbuf().scale_simple(w, h, GdkPixbuf.InterpType.TILES)
			self.get_image().set_main_pixbuf(pb)
			self.restore_pixbuf()
			self.window.force_selection_tool()

	def update_temp_pixbuf(self):
		w = self.get_width()
		h = self.get_height()
		if self.scale_selection:
			pb = self.get_selection_pixbuf().scale_simple(w, h, GdkPixbuf.InterpType.TILES)
		else:
			pb = self.get_main_pixbuf().scale_simple(w, h, GdkPixbuf.InterpType.TILES)
		self.get_image().set_temp_pixbuf(pb)

	def on_tool_selected(self, *args):
		self.scale_selection = (self.window.hijacker_id is not None)
		if self.scale_selection:
			w = self.get_selection_pixbuf().get_width()
			h = self.get_selection_pixbuf().get_height()
		else:
			w = self.get_image().get_pixbuf_width()
			h = self.get_image().get_pixbuf_height()
		self.set_keep_proportions() # XXX redondant ?
		self.width_btn.set_value(w)
		self.height_btn.set_value(h)

	def on_width_changed(self, *args):
		if self.keep_proportions:
			if self.proportion != self.get_width()/self.get_height():
				self.height_btn.set_value(self.get_width()/self.proportion)
		self.update_area()

	def on_height_changed(self, *args):
		if self.keep_proportions:
			if self.proportion != self.get_width()/self.get_height():
				self.width_btn.set_value(self.get_height()*self.proportion)
		else:
			self.update_area()

	def update_area(self):
		self.update_temp_pixbuf()
		# if self.scale_selection:
		# 	self.set_edition_state('temp-as-selection')
		# else:
		# 	self.set_edition_state('temp-as-main')
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

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color, event_x, event_y):
		self.x_press = event.x
		self.y_press = event.y

	def adapt_to_window_size(self):
		available_width = self.window.bottom_panel_box.get_allocated_width()
		if self.centered_box.get_orientation() == Gtk.Orientation.HORIZONTAL:
			self.needed_width_for_long = self.centered_box.get_preferred_width()[0] + \
				self.cancel_btn.get_allocated_width() + \
				self.apply_btn.get_allocated_width()
		if self.needed_width_for_long > 0.8 * available_width:
			self.centered_box.set_orientation(Gtk.Orientation.VERTICAL)
		else:
			self.centered_box.set_orientation(Gtk.Orientation.HORIZONTAL)
