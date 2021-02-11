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
		super().__init__('censor', _("Censor"), 'tool-censor-symbolic', window)
		self.use_operator = True
		self.row.get_style_context().add_class('destructive-action')

		self.add_tool_action_enum('censor-type', 'blur')
		self._set_options_attributes() # Not optimal but more readable

	def get_options_label(self):
		return _("Censoring options")

	def _set_options_attributes(self):
		self._censor_type = self.get_option_value('censor-type')

	def get_edition_status(self):
		self._set_options_attributes()
		return self.label

	############################################################################

	def on_press_on_area(self, event, surface, event_x, event_y):
		self.set_common_values(event.button, event_x, event_y)

	def on_motion_on_area(self, event, surface, event_x, event_y):
		operation = self.build_operation(event_x, event_y, True)
		self.do_tool_operation(operation)

	def on_release_on_area(self, event, surface, event_x, event_y):
		operation = self.build_operation(event_x, event_y, False)
		self.apply_operation(operation)

	############################################################################

	def build_operation(self, event_x, event_y, is_preview):
		operation = {
			'tool_id': self.id,
			'line_width': self.tool_width,
			'censor-type': self._censor_type,
			'is_preview': is_preview,
			'x_release': event_x,
			'y_release': event_y,
			'x_press': self.x_press,
			'y_press': self.y_press
		}
		return operation

	def do_tool_operation(self, operation):
		cairo_context = self.start_tool_operation(operation)
		censor_type = operation['censor-type']
		line_width = operation['line_width']
		cairo_context.set_line_width(line_width)
		x1 = operation['x_press']
		y1 = operation['y_press']
		x2 = operation['x_release']
		y2 = operation['y_release']

		# We don't memorize the path because all coords are here anyway for the
		# surface clipping.
		cairo_context.move_to(x1, y1)
		cairo_context.line_to(x2, y2)

		# self.stroke_with_operator(operation['operator'], cairo_context, \
		#                                     line_width, operation['is_preview'])
		# FIXME TODO

		# is_blur = (operator == cairo.Operator.DEST_IN)
		# if is_blur and is_preview:
		# 	context.set_operator(cairo.Operator.CLEAR)

		# if is_blur and not is_preview:
		# 	context.set_line_width(line_width)
		# 	context.stroke_preserve()
		# 	radius = int(line_width / 2)
		# 	source_surface = self.get_surface()
			# XXX using the whole surface is suboptimal
		# 	blurred_surface = utilities_blur_surface(source_surface, radius, 3, 0)
			# where 0 == BlurType.CAIRO_REPAINTS and 0 == BlurDirection.BOTH
		# 	self.restore_pixbuf()
		# 	context = self.get_context()
		# 	context.set_operator(cairo.Operator.OVER)
		# 	context.set_source_surface(blurred_surface, 0, 0)
		# 	context.paint()

	############################################################################
################################################################################

