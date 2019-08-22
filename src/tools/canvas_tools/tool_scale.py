# tool_scale.py
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
import cairo

from .abstract_canvas_tool import AbstractCanvasTool
from .bottombar import DrawingAdaptativeBottomBar

from .utilities import utilities_add_px_to_spinbutton

class ToolScale(AbstractCanvasTool):
	__gtype_name__ = 'ToolScale'

	def __init__(self, window):
		super().__init__('scale', _("Scale"), 'tool-scale-symbolic', window)
		self.cursor_name = 'se-resize'
		self.keep_proportions = False
		self.x_press = 0
		self.y_press = 0

	def try_build_panel(self):
		self.panel_id = 'scale'
		self.window.options_manager.try_add_bottom_panel(self.panel_id, self)

	def build_bottom_panel(self):
		bar = ScaleToolPanel(self.window)
		self.width_btn = bar.width_btn
		self.height_btn = bar.height_btn
		self.proportions_btn = bar.proportions_btn
		self.width_btn.connect('value-changed', self.on_width_changed)
		self.height_btn.connect('value-changed', self.on_height_changed)
		self.proportions_btn.connect('toggled', self.set_keep_proportions)
		return bar

	def get_edition_status(self):
		if self.apply_to_selection:
			return _("Scaling the selection")
		else:
			return _("Scaling the canvas")

	############################################################################

	def set_keep_proportions(self, *args):
		self.keep_proportions = self.proportions_btn.get_active()
		if self.keep_proportions:
			self.proportion = self.get_width()/self.get_height()

	def on_tool_selected(self, *args):
		super().on_tool_selected()
		self.keep_proportions = False
		if self.apply_to_selection:
			w = self.get_selection_pixbuf().get_width()
			h = self.get_selection_pixbuf().get_height()
		else:
			w = self.get_image().get_pixbuf_width()
			h = self.get_image().get_pixbuf_height()
		self.width_btn.set_value(w)
		self.height_btn.set_value(h)
		self.keep_proportions = self.proportions_btn.get_active()
		self.proportion = w/h

	def on_width_changed(self, *args):
		if self.keep_proportions:
			if self.proportion != self.get_width()/self.get_height():
				self.height_btn.set_value(self.get_width()/self.proportion)
		self.update_temp_pixbuf()

	def on_height_changed(self, *args):
		if self.keep_proportions:
			if self.proportion != self.get_width()/self.get_height():
				self.width_btn.set_value(self.get_height()*self.proportion)
		else:
			self.update_temp_pixbuf()

	def get_width(self):
		return self.width_btn.get_value_as_int()

	def get_height(self):
		return self.height_btn.get_value_as_int()

	def on_press_on_area(self, area, event, surface, event_x, event_y):
		self.x_press = event.x
		self.y_press = event.y

	def on_motion_on_area(self, area, event, surface, event_x, event_y):
		delta_x = event.x - self.x_press
		self.width_btn.set_value(self.width_btn.get_value() + delta_x)
		if not self.keep_proportions:
			delta_y = event.y - self.y_press
			self.height_btn.set_value(self.height_btn.get_value() + delta_y)
		self.x_press = event.x
		self.y_press = event.y

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'is_selection': self.apply_to_selection,
			'is_preview': True,
			'width': self.get_width(),
			'height': self.get_height()
		}
		return operation

	def do_tool_operation(self, operation):
		if operation['tool_id'] != self.id:
			return
		self.restore_pixbuf()

		if operation['is_selection']:
			source_pixbuf = self.get_selection_pixbuf()
		else:
			source_pixbuf = self.get_main_pixbuf()
		self.get_image().set_temp_pixbuf(source_pixbuf.scale_simple( \
		   operation['width'], operation['height'], GdkPixbuf.InterpType.TILES))
		self.common_end_operation(operation['is_preview'], operation['is_selection'])

	############################################################################
################################################################################

class ScaleToolPanel(DrawingAdaptativeBottomBar):
	__gtype_name__ = 'ScaleToolPanel'

	def __init__(self, window):
		super().__init__()
		self.window = window
		builder = self.build_ui('tools/ui/tool_scale.ui')
		# ... TODO
		#
		# bar.widgets_narrow = []
		# bar.widgets_wide = []
		#
		# self.centered_box = builder.get_object('centered_box')
		# self.cancel_btn = builder.get_object('cancel_btn')
		# self.apply_btn = builder.get_object('apply_btn')

		self.width_btn = builder.get_object('width_btn')
		self.height_btn = builder.get_object('height_btn')
		utilities_add_px_to_spinbutton(self.height_btn, 4, 'px')
		utilities_add_px_to_spinbutton(self.width_btn, 4, 'px')

		self.proportions_btn = builder.get_object('proportions_btn')

	# def ...(self, *args):
	# 	... TODO

	############################################################################
################################################################################

