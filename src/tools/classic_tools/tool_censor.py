# tool_censor.py
#
# Copyright 2018-2021 Romain F. T.
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
from .abstract_classic_tool import AbstractClassicTool
from .utilities_paths import utilities_add_arrow_triangle

class ToolCensor(AbstractClassicTool):
	__gtype_name__ = 'ToolCensor'

	def __init__(self, window, **kwargs):
		# Context: a tool to hide things like text. You can translate it as
		# "hide informations" if you think "censor" has a negative connotation
		super().__init__('censor', _("Censor"), 'tool-censor-symbolic', window)
		self.use_operator = True
		self.row.get_style_context().add_class('destructive-action')

		self.add_tool_action_enum('censor-type', 'mosaic')
		self._set_options_attributes() # Not optimal but more readable

	def get_options_label(self):
		return _("Censoring options")

	def _set_options_attributes(self):
		state_as_string = self.get_option_value('censor-type')
		self._censor_type = state_as_string
		if state_as_string == 'blur':
			self._censor_label = _("Blur")
		elif state_as_string == 'shuffle':
			self._censor_label = _("Shuffle pixels")
		elif state_as_string == 'mixed':
			self._censor_label = _("Shuffle and blur")
		elif state_as_string == 'mosaic':
			self._censor_label = _("Mosaic")
		else: # if state_as_string == 'solid':
			self._censor_label = _("Solid color")

	def get_edition_status(self):
		self._set_options_attributes()
		return self.label + ' - ' + self._censor_label

	############################################################################

	def on_press_on_area(self, event, surface, event_x, event_y):
		self.set_common_values(event.button, event_x, event_y)

	def on_motion_on_area(self, event, surface, event_x, event_y):
		self._draw_rectangle(event_x, event_y)
		operation = self.build_operation(self._path, False)
		self.do_tool_operation(operation)

	def on_release_on_area(self, event, surface, event_x, event_y):
		self._draw_rectangle(event_x, event_y)
		operation = self.build_operation(self._path, True)
		self.apply_operation(operation)
		self._reset_temp_points()

	def _draw_rectangle(self, event_x, event_y):
		cairo_context = self.get_context()
		cairo_context.move_to(self.x_press, self.y_press)
		cairo_context.line_to(self.x_press, event_y)
		cairo_context.line_to(event_x, event_y)
		cairo_context.line_to(event_x, self.y_press)
		cairo_context.close_path()
		self._path = cairo_context.copy_path()

	def _reset_temp_points(self):
		self._path = None
		self.x_press = -1.0
		self.y_press = -1.0

	############################################################################

	def build_operation(self, path, is_preview):
		operation = {
			'tool_id': self.id,
			'noise': self.tool_width,
			'rgba': self.main_color,
			'censor-type': self._censor_type,
			'is_preview': is_preview,
			'path': path
		}
		return operation

	def do_tool_operation(self, operation):
		cairo_context = self.start_tool_operation(operation)
		censor_type = operation['censor-type']

		if operation['is_preview'] or censor_type == 'solid':
			pass
			# TODO fill the path with rgba
			return

		# TODO define a pixbuf from the path

		if censor_type == 'mosaic':
			pass # TODO call the tiled blur
		elif censor_type == 'blur':
			pass # TODO call the slow blur
		elif censor_type == 'shuffle':
			pass # TODO call an utility that'll shuffle the pixels
		elif censor_type == 'mixed':
			pass # TODO call that utility + the fast blur

		# TODO paint the pixbuf on the normal surface

	############################################################################
################################################################################

