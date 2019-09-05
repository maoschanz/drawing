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
		self.add_tool_action_boolean('scale-proportions', True)
		# self.add_tool_action_boolean('scale-deformation-h', False) # TODO
		# self.add_tool_action_boolean('scale-deformation-v', False) # TODO

	def try_build_panel(self):
		self.panel_id = 'scale'
		self.window.options_manager.try_add_bottom_panel(self.panel_id, self)

	def build_bottom_panel(self):
		bar = ScaleToolPanel(self.window, self)
		self.width_btn = bar.width_btn
		self.height_btn = bar.height_btn
		self.width_btn.connect('value-changed', self.on_width_changed)
		self.height_btn.connect('value-changed', self.on_height_changed)
		return bar

	def get_edition_status(self):
		if self.apply_to_selection:
			return _("Scaling the selection")
		else:
			return _("Scaling the canvas")

	############################################################################

	def try_set_keep_proportions(self, *args):
		# XXX this shit is a clue that this tool is not enough operation-ish
		if self.keep_proportions == self.get_option_value('scale-proportions'):
			return
		self.keep_proportions = self.get_option_value('scale-proportions')
		if self.keep_proportions:
			self.proportion = self.get_width()/self.get_height()

	def on_tool_selected(self, *args):
		super().on_tool_selected()
		if self.apply_to_selection:
			width = self.get_selection_pixbuf().get_width()
			height = self.get_selection_pixbuf().get_height()
		else:
			width = self.get_image().get_pixbuf_width()
			height = self.get_image().get_pixbuf_height()
		self.keep_proportions = self.get_option_value('scale-proportions')
		self.proportion = width/height
		self.width_btn.set_value(width)
		self.height_btn.set_value(height)

	def on_width_changed(self, *args):
		self.try_set_keep_proportions()
		if self.keep_proportions:
			if self.proportion != self.get_width()/self.get_height():
				self.height_btn.set_value(self.get_width()/self.proportion)
		self.update_temp_pixbuf()

	def on_height_changed(self, *args):
		self.try_set_keep_proportions()
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

	def __init__(self, window, scale_tool):
		super().__init__()
		self.window = window
		# knowing the tool is needed because the panel doesn't compact the same
		# way if it's applied to the selection
		self.scale_tool = scale_tool
		builder = self.build_ui('tools/ui/tool_scale.ui')

		self.width_btn = builder.get_object('width_btn')
		self.height_btn = builder.get_object('height_btn')
		utilities_add_px_to_spinbutton(self.height_btn, 4, 'px')
		utilities_add_px_to_spinbutton(self.width_btn, 4, 'px')

		self.width_label = builder.get_object('width_label')
		self.height_label = builder.get_object('height_label')

		self.separator = builder.get_object('separator')
		self.options_btn = builder.get_object('options_btn')

	def toggle_options_menu(self):
		self.options_btn.set_active(not self.options_btn.get_active())

	def init_adaptability(self):
		super().init_adaptability()
		temp_limit_size = self.centered_box.get_preferred_width()[0] + \
		                    self.cancel_btn.get_preferred_width()[0] + \
		                     self.apply_btn.get_preferred_width()[0]
		self.set_limit_size(temp_limit_size)

	def set_compact(self, state):
		super().set_compact(state)
		if state:
			self.centered_box.set_orientation(Gtk.Orientation.VERTICAL)
		else:
			self.centered_box.set_orientation(Gtk.Orientation.HORIZONTAL)
		self.width_label.set_visible(not state)
		self.height_label.set_visible(not state)
		self.separator.set_visible(not state)

		# if self.scale_tool.apply_to_selection:
		# 	self.???.set_visible(state)
		# else:
		# 	self.???.set_visible(state)

	############################################################################
################################################################################

