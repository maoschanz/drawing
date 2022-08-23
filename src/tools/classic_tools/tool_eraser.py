# tool_eraser.py
#
# Copyright 2018-2022 Romain F. T.
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

import cairo
from gi.repository import Gdk, GdkPixbuf
from .abstract_classic_tool import AbstractClassicTool

from .eraser_area import EraserArea
from .eraser_color import EraserColor
from .eraser_rubber import EraserRubber

class ToolEraser(AbstractClassicTool):
	__gtype_name__ = 'ToolEraser'

	def __init__(self, window, **kwargs):
		# Context: this is the name of a tool
		super().__init__('eraser', _("Eraser"), 'tool-eraser-symbolic', window)
		self.use_operator = False
		self._fallback_operator = 'clear'
		self.load_tool_action_enum('eraser-shape', 'last-eraser-type')
		self.load_tool_action_enum('selection-color', 'last-delete-replace')
		self.add_tool_action_enum('eraser-type', 'mosaic')
		self._rgba = [0.0, 0.0, 0.0, 0.0]

		self._erasers = {
			'rubber': EraserRubber(),
			'rectangle': EraserArea(self),
			'color': EraserColor(self),
		}

	def get_editing_tips(self):
		self._rgba_type = self.get_option_value('selection-color')
		self._eraser_shape = self.get_option_value('eraser-shape')
		self._apply_shape_constraints()

		opt = {
			'selection-color': self._rgba_type,
			'eraser-type': self._eraser_type
		}
		label_options = self.label + " - " + self.get_eraser().get_label_options(opt)

		if self.get_image().get_mouse_is_pressed():
			label_modifier_shift = None
		else:
			label_modifier_shift = self.label + " - "
			if self._eraser_shape == 'rectangle':
				label_modifier_shift += _("Press <Shift> to erase a path instead")
			else:
				label_modifier_shift += _("Press <Shift> to erase a rectangle area instead")
		# XXX ^ pas très ooc mais je sais même pas si on garde le fonctionnement

		full_list = [label_options, label_modifier_shift]
		return list(filter(None, full_list))

	def get_options_label(self):
		return _("Eraser options")

	def _apply_shape_constraints(self):
		self._eraser_type = self.get_option_value('eraser-type')

		can_blur = 'rectangle' == self._eraser_shape
		self.set_action_sensitivity('eraser-type', can_blur)
		if not can_blur:
			self._eraser_type = 'solid'

		use_solid_color = ('solid' == self._eraser_type) and \
		                                         ('color' != self._eraser_shape)
		self.set_action_sensitivity('selection-color', use_solid_color)
		if use_solid_color and 'secondary' == self._rgba_type:
			self._fallback_operator = 'source'
		else:
			self._fallback_operator = 'clear'
			# TODO en pratique non il y a des cas où on est plutôt en train de
			# flouter, il faudrait un elif, et un autre système pour l'opérateur
			# en fallback qui afficherait l'icône avec les gouttes.
			# En fait on devrait yeet le délire du `_fallback_operator` ?

		self.use_size = self.get_eraser().use_size()
		self.window.options_manager.update_pane(self)

	def give_back_control(self, should_preserve_selection):
		self.set_action_sensitivity('selection-color', True)

	def get_eraser(self):
		return self._erasers[self._eraser_shape]

	############################################################################

	def on_press_on_area(self, event, surface, event_x, event_y):
		self.set_common_values(event.button, event_x, event_y)
		self._path = None

		if self._rgba_type == 'alpha':
			self._rgba = [0.0, 0.0, 0.0, 0.0]
		elif self._rgba_type == 'initial':
			clr = self.get_image().get_initial_rgba()
			self._rgba = [clr.red, clr.green, clr.blue, clr.alpha]
		elif self._rgba_type == 'secondary':
			self._rgba = self.secondary_color

		self.update_modifier_state(event.state)
		if 'SHIFT' in self._modifier_keys:
			if self._eraser_shape == 'rectangle':
				self._eraser_shape = 'rubber'
			else:
				self._eraser_shape = 'rectangle'
			self._apply_shape_constraints()

	def on_motion_on_area(self, event, surface, event_x, event_y, render=True):
		cairo_context = self.get_context()
		self._path = self.get_eraser().on_motion(cairo_context, \
		           [self.x_press, self.y_press], [event_x, event_y], self._path)

		if not render:
			return
		operation = self.build_operation(True)
		self.do_tool_operation(operation)

	def on_release_on_area(self, event, surface, event_x, event_y):
		cairo_context = self.get_context()
		self._path = self.get_eraser().on_release(cairo_context, \
		           [self.x_press, self.y_press], [event_x, event_y], self._path)
		operation = self.build_operation(False)
		self.apply_operation(operation)
		self._reset_temp_points()

	def _reset_temp_points(self):
		self._path = None
		self.x_press = -1.0
		self.y_press = -1.0

	############################################################################

	def build_operation(self, is_preview):
		if is_preview:
			eraser_type = 'solid'
		else:
			eraser_type = self._eraser_type
		operation = {
			'tool_id': self.id,
			'is_preview': is_preview,
			'line_width': self.tool_width,
			'replacement': self._rgba,
			'censor-type': eraser_type,
			'censor-shape': self._eraser_shape,
			'antialias': self._use_antialias,
			'path': self._path
		}
		return operation

	def do_tool_operation(self, operation):
		# depending on the implementation, the "path" might not be a cairo.Path
		if operation['path'] is None:
			return
		cairo_context = self.start_tool_operation(operation)
		eraser_id = operation['censor-shape']
		self._erasers[eraser_id].do_operation(cairo_context, operation)

	############################################################################
################################################################################

