# tool_eraser.py
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

import cairo, random
from gi.repository import Gdk, GdkPixbuf
from .tool_pencil import ToolPencil
from .abstract_classic_tool import AbstractClassicTool
from .utilities_paths import utilities_smooth_path
from .utilities_blur import utilities_blur_surface, BlurType, BlurDirection

class ToolEraser(ToolPencil):
	__gtype_name__ = 'ToolEraser'

	def __init__(self, window, **kwargs):
		super().__init__(window)
		# Context: this is the name of a tool, in the meaning "a rubber eraser"
		AbstractClassicTool.__init__(self, 'eraser', _("Eraser"), \
		                                         'tool-eraser-symbolic', window)
		self.use_operator = False
		self._fallback_operator = 'clear'
		self.load_tool_action_enum('selection-color', 'last-delete-replace')
		self.add_tool_action_enum('eraser-type', 'mosaic')
		self.add_tool_action_enum('eraser-shape', 'pencil')
		self._rgba = [0.0, 0.0, 0.0, 0.0]

	def get_edition_status(self):
		self._eraser_type = self.get_option_value('eraser-type')
		self._rgba_type = self.get_option_value('selection-color')
		self._eraser_shape = self.get_option_value('eraser-shape')

		can_blur = self._eraser_shape != 'pencil'
		self.set_action_sensitivity('eraser-type', can_blur)
		if not can_blur:
			self._eraser_type = 'solid'

		if 'solid' == self._eraser_type and 'secondary' == self._rgba_type:
			self._fallback_operator = 'source'
		else:
			self._fallback_operator = 'clear'
			# TODO en pratique non il y a des cas où on est plutôt en train de
			# flouter, il faudrait un elif, et un autre système pour l'opérateur
			# en fallback qui afficherait l'icône avec les gouttes.
			# En fait on devrait yeet le délire du `_fallback_operator` ?
		self.window.options_manager.update_pane(self)

		label = self.label
		if self._eraser_shape == 'pencil':
			label += ' - ' + _("Pencil")
		else:
			label += ' - ' + _("Rectangle")
		if self._eraser_type == 'solid':
			label += ' - ' + {
				'alpha': _("Transparency"),
				'initial': _("Default color"),
				'secondary': _("Secondary color")
			}[self._rgba_type]
		else:
			label += ' - ' + {
				'blur': _("Blur"),
				'shuffle': _("Shuffle pixels"),
				'mixed': _("Shuffle and blur"),
				'mosaic': _("Mosaic")
			}[self._eraser_type]
		return label

	def get_options_label(self):
		return _("Eraser options")

	############################################################################

	def on_press_on_area(self, event, surface, event_x, event_y):
		super().on_press_on_area(event, surface, event_x, event_y)

		if self._rgba_type == 'alpha':
			self._rgba = [0.0, 0.0, 0.0, 0.0]
		elif self._rgba_type == 'initial':
			clr = self.get_image().get_initial_rgba()
			self._rgba = [clr.red, clr.green, clr.blue, clr.alpha]
		elif self._rgba_type == 'secondary':
			clr = self.secondary_color
			self._rgba = [clr.red, clr.green, clr.blue, clr.alpha]

	def on_motion_on_area(self, event, surface, event_x, event_y, render=True):
		if self._eraser_shape == 'rectangle':
			self._draw_rectangle(event_x, event_y)
		else:
			self._add_point(event_x, event_y)
		if render:
			operation = self.build_operation(True)
			self.do_tool_operation(operation)

	def on_release_on_area(self, event, surface, event_x, event_y):
		if self._eraser_shape == 'rectangle':
			self._draw_rectangle(event_x, event_y)
		else:
			self._add_point(event_x, event_y)
		operation = self.build_operation(False)
		self.apply_operation(operation)
		self._reset_temp_points()

	def _draw_rectangle(self, event_x, event_y):
		cairo_context = self.get_context()
		cairo_context.move_to(int(self.x_press), int(self.y_press))
		cairo_context.line_to(int(self.x_press), int(event_y))
		cairo_context.line_to(int(event_x), int(event_y))
		cairo_context.line_to(int(event_x), int(self.y_press))
		cairo_context.close_path()
		self._path = cairo_context.copy_path()

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
			'line_cap': self._cap_id,
			'line_join': self._join_id,
			'replacement': self._rgba,
			'censor-type': eraser_type,
			'censor-shape': self._eraser_shape,
			'antialias': self._use_antialias,
			'path': self._path
		}
		return operation

	def do_tool_operation(self, operation):
		if operation['path'] is None:
			return
		cairo_context = self.start_tool_operation(operation)
		cairo_context.set_operator(cairo.Operator.SOURCE)
		censor_type = operation['censor-type']

		if censor_type == 'solid':
			cairo_context.set_source_rgba(*operation['replacement'])
			if operation['censor-shape'] == 'rectangle':
				cairo_context.append_path(operation['path'])
				cairo_context.fill()
			else:
				cairo_context.set_line_cap(cairo.LineCap.ROUND)
				cairo_context.set_line_join(cairo.LineJoin.ROUND)
				cairo_context.set_line_width(operation['line_width'])
				utilities_smooth_path(cairo_context, operation['path'])
				cairo_context.stroke()
			return
		else:
			cairo_context.append_path(operation['path'])

		[r0, r1, r2, r3] = cairo_context.path_extents()
		[r0, r1, r2, r3] = [int(r0), int(r1), int(r2), int(r3)]
		width = r2 - r0
		height = r3 - r1
		surface = cairo.ImageSurface(cairo.Format.ARGB32, width, height)
		ccontext2 = cairo.Context(surface)
		ccontext2.set_source_surface(self.get_surface(), -1 * r0, -1 * r1)
		ccontext2.paint()
		scale = self.scale_factor()
		surface.set_device_scale(scale, scale)

		b_rad = min(15, int(min(width, height) / 4))
		b_dir = BlurDirection.BOTH
		shuffle_intensity = int((width * height) / 2)
		if censor_type == 'mosaic':
			bs = utilities_blur_surface(surface, b_rad, BlurType.TILES, b_dir)
		elif censor_type == 'blur':
			bs = utilities_blur_surface(surface, b_rad, BlurType.PX_BOX, b_dir)
		elif censor_type == 'shuffle':
			bs = self._shuffle_pixels(surface, shuffle_intensity)
		elif censor_type == 'mixed':
			bs = self._shuffle_pixels(surface, shuffle_intensity / 2)
			bs = utilities_blur_surface(bs, b_rad, BlurType.CAIRO_REPAINTS, b_dir)

		cairo_context.clip()
		# XXX this ^ doesn't work with the 'pencil' shape, which forces me to
		# disable the 'eraser-type' option in this case
		cairo_context.set_source_surface(bs, r0, r1)
		cairo_context.paint()

	############################################################################

	def _shuffle_pixels(self, surface, iterations):
		w = surface.get_width()
		h = surface.get_height()
		channels = 4 # ARGB
		if w <= 1 or h <= 1:
			return surface

		pixels = surface.get_data()

		random.seed(1)
		while iterations > 0:
			iterations = iterations - 1
			self._shuffle_one_iteration(w, h, channels, pixels)
		return surface

	def _shuffle_one_iteration(self, w, h, channels, pixels):
		pix1_x = random.randint(0, w - 1)
		pix1_y = random.randint(0, h - 1)

		# Get data for a first pixel
		cur_pixel = (pix1_y * w + pix1_x) * channels
		a1 = pixels[cur_pixel + 0]
		r1 = pixels[cur_pixel + 1]
		g1 = pixels[cur_pixel + 2]
		b1 = pixels[cur_pixel + 3]

		pix2_x = random.randint(0, w - 1)
		pix2_y = random.randint(0, h - 1)

		# Get data for a second pixel
		cur_pixel = (pix2_y * w + pix2_x) * channels
		a2 = pixels[cur_pixel + 0]
		r2 = pixels[cur_pixel + 1]
		g2 = pixels[cur_pixel + 2]
		b2 = pixels[cur_pixel + 3]

		# Data of the 1st pixel is written in the 2nd one
		pixels[cur_pixel + 0] = a1
		pixels[cur_pixel + 1] = r1
		pixels[cur_pixel + 2] = g1
		pixels[cur_pixel + 3] = b1

		# Data of the 2nd pixel is written in the 1st one
		cur_pixel = (pix1_y * w + pix1_x) * channels
		pixels[cur_pixel + 0] = a2
		pixels[cur_pixel + 1] = r2
		pixels[cur_pixel + 2] = g2
		pixels[cur_pixel + 3] = b2

	############################################################################
################################################################################

