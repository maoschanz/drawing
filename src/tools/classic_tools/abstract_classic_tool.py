# abstract_classic_tool.py
#
# Copyright 2018-2020 Romain F. T.
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
from .abstract_tool import AbstractAbstractTool
from .classic_panel import ClassicToolPanel
from .blurring import utilities_fast_blur

class AbstractClassicTool(AbstractAbstractTool):
	__gtype_name__ = 'AbstractClassicTool'

	def __init__(self, tool_id, label, icon_name, window, **kwargs):
		super().__init__(tool_id, label, icon_name, window)
		self.menu_id = 0
		self.use_color = True
		self.use_size = True
		self.accept_selection = False
		self.tool_width = 10
		self.main_color = None
		self.secondary_color = None
		# self._use_antialias = True

	############################################################################
	# UI implementations #######################################################

	def try_build_panel(self):
		self.panel_id = 'classic'
		self.window.options_manager.try_add_bottom_panel(self.panel_id, self)

	def build_bottom_panel(self):
		return ClassicToolPanel(self.window)

	def on_tool_selected(self):
		# XXX shouldn't i update the label/menu/size/sensitivity/etc. here?
		pass

	############################################################################
	# Options ##################################################################

	def set_common_values(self, event_btn):
		# self._use_antialias = self.get_option_value('antialias')
		self.tool_width = self.window.options_manager.get_tool_width()
		if event_btn == 1:
			self.main_color = self.window.options_manager.get_left_color()
			self.secondary_color = self.window.options_manager.get_right_color()
		if event_btn == 3:
			self.main_color = self.window.options_manager.get_right_color()
			self.secondary_color = self.window.options_manager.get_left_color()

	def get_operator_enum(self):
		return self.window.options_manager.get_operator()[0]

	############################################################################
	# Operations common methods ################################################

	def stroke_with_operator(self, operator, context, line_width, is_preview):
		context.set_operator(operator)
		# if use_antialias: # à ajouter comme paramètre de cette méthode
		# 	context.set_antialias(cairo.Antialias.DEFAULT)
		# else:
		# 	context.set_antialias(cairo.Antialias.NONE)
		is_blur = (operator == cairo.Operator.DEST_IN)
		if is_blur and is_preview:
			context.set_operator(cairo.Operator.CLEAR)

		if is_blur and not is_preview:
			context.set_line_width(2*line_width)
			context.stroke()
			radius = int(line_width/2)
			# TODO only give the adequate rectangle, not the whole image, it's too slow!
			b_surface = utilities_fast_blur(self.get_surface(), radius, 0)
			# where 0 == BlurType.AUTO
			self.restore_pixbuf()
			context = self.get_context()
			context.set_operator(cairo.Operator.OVER)
			context.set_source_surface(b_surface, 0, 0)
			context.paint()
		else:
			context.set_line_width(line_width)
			context.stroke()

	############################################################################
################################################################################
