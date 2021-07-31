# tool_skew.py
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

from gi.repository import Gdk
from .abstract_transform_tool import AbstractCanvasTool
from .optionsbar_skew import OptionsBarSkew

class ToolSkew(AbstractCanvasTool):
	__gtype_name__ = 'ToolSkew'

	def __init__(self, window):
		# In this context, "Skew" is the name of the tool changing rectangles
		# into parallelograms (= tilt, slant, bend). Named after MS Paint's
		# "Stretch/Skew" dialog.
		super().__init__('skew', _("Skew"), 'tool-skew-symbolic', window)

	def try_build_pane(self):
		self.pane_id = 'skew'
		self.window.options_manager.try_add_bottom_pane(self.pane_id, self)

	def build_bottom_pane(self):
		bar = OptionsBarSkew()
		self.yx_spinbtn = bar.yx_spinbtn
		self.xy_spinbtn = bar.xy_spinbtn
		self.yx_spinbtn.connect('value-changed', self.on_coord_changed)
		self.xy_spinbtn.connect('value-changed', self.on_coord_changed)
		return bar

	# def get_options_label(self):
	# 	return _("Skewing options")

	# def get_edition_status(self):
	# 	if self.apply_to_selection:
	# 		return _("Skew the selection")
	# 	else:
	# 		return _("Skew the canvas")

	def on_tool_selected(self, *args):
		super().on_tool_selected()
		self._reset_values()

	############################################################################

	# TODO surface signals

	def on_coord_changed(self, *args):
		self.build_and_do_op()

	def _reset_values(self, *args):
		self.yx_spinbtn.set_value(0)
		self.xy_spinbtn.set_value(0)
		self.build_and_do_op()

	############################################################################

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'is_selection': self.apply_to_selection,
			'is_preview': True,
			'local_dx': 0,
			'local_dy': 0,
			'yx': self.yx_spinbtn.get_value_as_int()/100,
			'xy': self.xy_spinbtn.get_value_as_int()/100,
		}
		return operation

	def do_tool_operation(self, operation):
		self.start_tool_operation(operation)
		if operation['is_selection']:
			source_pixbuf = self.get_selection_pixbuf()
		else:
			source_pixbuf = self.get_main_pixbuf()
		source_surface = Gdk.cairo_surface_create_from_pixbuf(source_pixbuf, 0, None)
		source_surface.set_device_scale(self.scale_factor(), self.scale_factor())

		xy = operation['xy']
		x0 = 0.0
		if xy < 0:
			x0 = int(-1 * xy * source_surface.get_height())
		yx = operation['yx']
		y0 = 0.0
		if yx < 0:
			y0 = int(-1 * yx * source_surface.get_width())
		coefs = [1.0, yx, xy, 1.0, x0, y0]

		new_surface = self.get_deformed_surface(source_surface, coefs)
		new_pixbuf = Gdk.pixbuf_get_from_surface(new_surface, 0, 0, \
		                      new_surface.get_width(), new_surface.get_height())
		self.get_image().set_temp_pixbuf(new_pixbuf)
		self.common_end_operation(operation)

	############################################################################
################################################################################

