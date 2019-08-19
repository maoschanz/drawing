# tool_matrix.py
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
import cairo, math

from .abstract_canvas_tool import AbstractCanvasTool
from .bottombar import DrawingAdaptativeBottomBar

class ToolMatrix(AbstractCanvasTool):
	__gtype_name__ = 'ToolMatrix'

	def __init__(self, window):
		super().__init__('matrix', _("Deformation"), 'applications-science-symbolic', window)
		# self.cursor_name = ''
		self.row.get_style_context().add_class('destructive-action')

		self.apply_to_selection = False
		self.dont_update = False
		self.add_tool_action_simple('matrix-reset', self.on_reset_values)

	def get_edition_status(self):
		return "You're not supposed to use this tool (development only)."

	def on_tool_selected(self, *args):
		super().on_tool_selected()
		self.on_reset_values()

# TODO
# le but est de remplacer :
# - rotate
# - flip
# - scale
# et d'introduire des features telles que :
# - l'inclinaison comme dans Microsoft Paint
# - les widgets sur la surface ?

	def try_build_panel(self):
		self.panel_id = 'matrix'
		self.window.options_manager.try_add_bottom_panel(self.panel_id, self)

	def build_bottom_panel(self):
		bar = DrawingAdaptativeBottomBar()
		builder = bar.build_ui('tools/ui/tool_matrix.ui')

		self.angle_spinbtn = builder.get_object('angle_spinbtn')
		self.angle_spinbtn.connect('value-changed', self.on_angle_changed)

		self.xx_spinbtn = builder.get_object('xx_spinbtn')
		self.xx_spinbtn.connect('value-changed', self.on_coord_changed)

		self.yx_spinbtn = builder.get_object('yx_spinbtn')
		self.yx_spinbtn.connect('value-changed', self.on_coord_changed)

		self.xy_spinbtn = builder.get_object('xy_spinbtn')
		self.xy_spinbtn.connect('value-changed', self.on_coord_changed)

		self.yy_spinbtn = builder.get_object('yy_spinbtn')
		self.yy_spinbtn.connect('value-changed', self.on_coord_changed)

		self.x0_spinbtn = builder.get_object('x0_spinbtn')
		self.x0_spinbtn.connect('value-changed', self.on_coord_changed)

		self.y0_spinbtn = builder.get_object('y0_spinbtn')
		self.y0_spinbtn.connect('value-changed', self.on_coord_changed)

		return bar

	############################################################################

	def on_reset_values(self, *args):
		self.dont_update = True
		self.xx_spinbtn.set_value(100)
		self.xy_spinbtn.set_value(0)
		self.yx_spinbtn.set_value(0)
		self.yy_spinbtn.set_value(100)
		self.x0_spinbtn.set_value(0)
		self.y0_spinbtn.set_value(0)
		self.angle_spinbtn.set_value(0)
		self.dont_update = False
		self.on_coord_changed()

	# def on_flip_h(self, *args):
	# 	self.dont_update = True
		# TODO
	# 	self.dont_update = False
	# 	self.on_coord_changed()

	# def on_flip_v(self, *args):
	# 	self.dont_update = True
		# TODO
	# 	self.dont_update = False
	# 	self.on_coord_changed()

	def on_angle_changed(self, *args):
		self.dont_update = True
		angle = self.angle_spinbtn.get_value_as_int()
		rad = math.pi * angle / 180
		print(rad)
		xx = math.cos(rad)
		xy = math.sin(rad)
		yx = -1 * math.sin(rad)
		yy = math.cos(rad)
		x0 = 0 # TODO
		y0 = 0 # TODO
		self.xx_spinbtn.set_value(xx * 100)
		self.xy_spinbtn.set_value(xy * 100)
		self.yx_spinbtn.set_value(yx * 100)
		self.yy_spinbtn.set_value(yy * 100)
		# self.x0_spinbtn.set_value(x0)
		# self.y0_spinbtn.set_value(y0)

		x_old = 100
		y_old = 100
		x_new = xx * x_old + xy * y_old + x0
		y_new = yx * x_old + yy * y_old + y0
		print(x_new, y_new)

		self.dont_update = False
		self.on_coord_changed()

	def on_coord_changed(self, *args):
		if self.dont_update:
			print('no update')
			return
		print('update:')
		operation = self.build_operation()
		self.do_tool_operation(operation)

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'is_selection': self.apply_to_selection,
			'is_preview': True,
			'xx': self.xx_spinbtn.get_value_as_int()/100,
			'yx': self.yx_spinbtn.get_value_as_int()/100,
			'xy': self.xy_spinbtn.get_value_as_int()/100,
			'yy': self.yy_spinbtn.get_value_as_int()/100,
			'x0': self.x0_spinbtn.get_value_as_int(),
			'y0': self.y0_spinbtn.get_value_as_int()
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
		source_surface = Gdk.cairo_surface_create_from_pixbuf(source_pixbuf, 0, None)

		w = source_surface.get_width()
		h = source_surface.get_height()
		# surface = Gdk.cairo_surface_create_from_pixbuf(source_pixbuf, 0, None)
		surface = cairo.ImageSurface(cairo.Format.ARGB32, w, h)
		# surface = self.get_surface()

		cairo_context = cairo.Context(surface)
		# m = cairo.Matrix(xx=1.0, yx=0.0, xy=0.0, yy=1.0, x0=0.0, y0=0.0)
		m = cairo.Matrix(xx=operation['xx'], yx=operation['yx'], \
		                 xy=operation['xy'], yy=operation['yy'], \
		                 x0=operation['x0'], y0=operation['y0'])
		cairo_context.transform(m)
		cairo_context.set_source_surface(source_surface, 0, 0) # FIXME scroll and zoom
		# FIXME c'est ce "0, 0" qui charcute certains angles de rotation
		cairo_context.paint()

		new_pixbuf = Gdk.pixbuf_get_from_surface(surface, 0, 0, \
		                              surface.get_width(), surface.get_height())
		self.get_image().set_temp_pixbuf(new_pixbuf)
		self.common_end_operation(operation['is_preview'], operation['is_selection'])

	############################################################################
################################################################################

