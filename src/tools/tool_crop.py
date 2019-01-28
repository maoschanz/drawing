# crop.py
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
import cairo

from .tools import ToolTemplate

class ToolCrop(ToolTemplate):
	__gtype_name__ = 'ModeCrop'

	implements_panel = True

	def __init__(self, window):
		super().__init__('crop', _("Crop"), 'crop-symbolic', window)
		self.need_temp_pixbuf = True

		self.crop_selection = False
		self.x_press = 0
		self.y_press = 0
		self.move_instead_of_crop = False
		self.needed_width_for_long = 0

		self.add_tool_action_simple('crop_apply', self.on_apply)

		builder = Gtk.Builder.new_from_resource('/com/github/maoschanz/Drawing/tools/ui/tool_crop.ui')
		self.bottom_panel = builder.get_object('bottom-panel')
		self.centered_box = builder.get_object('centered_box')
		self.cancel_btn = builder.get_object('cancel_btn')
		self.apply_btn = builder.get_object('apply_btn')

		self.height_btn = builder.get_object('height_btn')
		self.width_btn = builder.get_object('width_btn')

		self.window.bottom_panel_box.add(self.bottom_panel)

	def get_panel(self):
		return self.bottom_panel

	def get_edition_status(self):
		if self.crop_selection:
			return _("Cropping the selection")
		else:
			return _("Cropping the canvas")

	def on_tool_selected(self, *args):
		self.crop_selection = (self.window.hijacker_id is not None)
		self._x = 0
		self._y = 0
		if self.crop_selection:
			self.init_if_selection()
		else:
			self.init_if_main()
		self.width_btn.connect('value-changed', self.on_width_changed)
		self.height_btn.connect('value-changed', self.on_height_changed)
		self.width_btn.set_value(self.original_width)
		self.height_btn.set_value(self.original_height)

	def init_if_selection(self):
		self.original_width = self.get_image().selection_pixbuf.get_width()
		self.original_height = self.get_image().selection_pixbuf.get_height()
		self.width_btn.set_range(1, self.original_width)
		self.height_btn.set_range(1, self.original_height)

	def init_if_main(self):
		self.original_width = self.get_image().get_pixbuf_width()
		self.original_height = self.get_image().get_pixbuf_height()
		self.width_btn.set_range(1, 10*self.original_width)
		self.height_btn.set_range(1, 10*self.original_height)

	def on_apply(self, *args):
		operation = self.build_operation()
		operation['pixbuf'] = self.get_selection_pixbuf().copy() # XXX uh ?
		#self.do_tool_operation(operation)
		self.apply_operation(operation)
		self.window.back_to_former_tool()

	def update_temp_pixbuf(self): # XXX doit fusionner avec le do_tool_operation ??
		if self.crop_selection:
			self.get_image().set_temp_pixbuf(self.get_selection_pixbuf().copy())
			x, y, width, height = self.validate_coords()
			self.crop_temp_pixbuf(x, y, width, height)
		else:
			self.get_image().temp_pixbuf = self.get_main_pixbuf().copy()
			x, y, width, height = self.validate_coords()
			self.crop_temp_pixbuf(x, y, width, height)
			self.scale_temp_pixbuf_to_area(width, height)
		self.non_destructive_show_modif()

		operation = self.build_operation() # XXX ne marche pas entièrement
		self.do_tool_operation(operation)

	def crop_temp_pixbuf(self, x, y, width, height):
		x = max(x, 0)
		y = max(y, 0)
		min_w = min(width, self.get_image().get_temp_pixbuf().get_width() - x)
		min_h = min(height, self.get_image().get_temp_pixbuf().get_height() - y)
		new_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, width, height)
		new_pixbuf.fill(0)
		self.get_image().temp_pixbuf.copy_area(x, y, min_w, min_h, new_pixbuf, 0, 0)
		self.get_image().temp_pixbuf = new_pixbuf

	def scale_temp_pixbuf_to_area(self, width, height):
		visible_w = self.get_image().get_allocated_width()
		visible_h = self.get_image().get_allocated_height()
		w_ratio = visible_w/width
		h_ratio = visible_h/height
		if w_ratio > 1.0 and h_ratio > 1.0:
			nice_w = width
			nice_h = height
		elif visible_h/visible_w > height/width:
			nice_w = visible_w
			nice_h = int(height * w_ratio)
		else:
			nice_w = int(width * h_ratio)
			nice_h = visible_h
		pb = self.get_image().get_temp_pixbuf()
		self.get_image().set_temp_pixbuf(pb.scale_simple(nice_w, nice_h, GdkPixbuf.InterpType.TILES))

	def get_width(self):
		return self.width_btn.get_value_as_int()

	def get_height(self):
		return self.height_btn.get_value_as_int()

	def on_width_changed(self, *args):
		self.update_temp_pixbuf()

	def on_height_changed(self, *args):
		self.update_temp_pixbuf()

	def on_motion_on_area(self, area, event, surface, event_x, event_y):
		delta_x = event.x - self.x_press
		delta_y = event.y - self.y_press
		if self.move_instead_of_crop:
			self._x = self._x - delta_x
			self._y = self._y - delta_y
		else:
			self.width_btn.set_value(self.width_btn.get_value() + delta_x)
			self.height_btn.set_value(self.height_btn.get_value() + delta_y)
		self.x_press = event.x
		self.y_press = event.y
		self.update_temp_pixbuf()

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color, event_x, event_y):
		self.x_press = event.x
		self.y_press = event.y
		self.move_instead_of_crop = (event.button == 3)

	def validate_coords(self):
		self._x = max(self._x, 0)
		self._y = max(self._y, 0)
		max_w = self.get_image().get_temp_pixbuf().get_width() - self.get_width()
		max_h = self.get_image().get_temp_pixbuf().get_height() - self.get_height()
		self._x = min(self._x, max_w)
		self._y = min(self._y, max_h)
		x = int(self._x)
		y = int(self._y)
		width = self.get_width()
		height = self.get_height()
		return x, y, width, height

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

###################################################

	def build_operation(self):
		#x, y, width, height = self.validate_coords() # XXX ?
		operation = {
			'tool_id': self.id,
			'is_selection': self.crop_selection,
			'pixbuf': None,
			'x': self._x,
			'y': self._y,
			'width': self.get_width(),
			'height': self.get_height()
		}
		return operation

	def do_tool_operation(self, operation):
		if operation['tool_id'] != self.id:
			return
		self.restore_pixbuf()
		cairo_context = cairo.Context(self.get_surface())
		if operation['is_selection']:
			cairo_context.set_source_surface(self.get_surface(), 0, 0)
			cairo_context.paint()
			self.get_image().delete_former_selection()
			Gdk.cairo_set_source_pixbuf(cairo_context, \
				self.get_image().get_temp_pixbuf(), \
				self.get_image().selection_x, \
				self.get_image().selection_y)
			cairo_context.paint()
		else:
			cairo_context.set_operator(cairo.Operator.CLEAR)
			cairo_context.paint()
			cairo_context.set_operator(cairo.Operator.OVER)
			Gdk.cairo_set_source_pixbuf(cairo_context, \
				self.get_image().get_temp_pixbuf(), \
				-1 * self.get_image().scroll_x, -1 * self.get_image().scroll_y)
			cairo_context.paint()
		self.non_destructive_show_modif()

	def apply_operation(self, operation): # fonctionne, mais l'historique ne marchera pas # TODO
		if operation['tool_id'] != self.id:
			return
		self.restore_pixbuf()
		if operation['is_selection']: # FIXME pas de préview
			self.window.get_selection_tool().crop_selection_surface(operation['x'], \
				operation['y'], operation['width'], operation['height'])
			#self.window.get_selection_tool().crop_selection_surface(x, y, width, height) # XXX à tester
			# XXX dois-je set le temp_pixbuf d'abord ????????
			# XXX quid du path ????????
			self.window.get_selection_tool().on_confirm_hijacked_modif()
		else:
			self.get_image().set_temp_pixbuf(self.get_main_pixbuf().copy())
			self.crop_temp_pixbuf(operation['x'], operation['y'], operation['width'], operation['height'])
			self.get_image().set_main_pixbuf(self.get_image().get_temp_pixbuf().copy())
			self.restore_pixbuf()
			self.apply_to_pixbuf()
