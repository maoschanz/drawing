# Licensed under GPL3 https://github.com/maoschanz/drawing/blob/master/LICENSE

import cairo, random
from .abstract_eraser import AbstractEraser
from .utilities_blur import utilities_blur_surface, BlurType, BlurDirection

class EraserArea(AbstractEraser):
	__gtype_name__ = 'EraserArea'

	def __init__(self, tool):
		super().__init__()
		self._tool = tool

	def get_label_options(self, options={}):
		label_options = _("Rectangle area")
		if options['eraser-type'] == 'solid':
			label_options += " - " + {
				'alpha': _("Transparency"),
				'initial': _("Default color"),
				'secondary': _("Secondary color")
			}[options['selection-color']]
		else:
			label_options += " - " + {
				'blur': _("Blur"),
				'shuffle': _("Shuffle pixels"),
				'mixed': _("Shuffle and blur"),
				'mosaic': _("Mosaic")
			}[options['eraser-type']]
		return label_options

	def get_active_options(self):
		return ['eraser-type', 'selection-color']

	def on_release(self, cairo_context, press, event, path=None):
		cairo_context.move_to(*press)
		cairo_context.line_to(press[0], event[1])
		cairo_context.line_to(*event)
		cairo_context.line_to(event[0], press[1])
		cairo_context.close_path()
		return cairo_context.copy_path()

	############################################################################

	def do_operation(self, cairo_context, operation):
		cairo_context.set_operator(cairo.Operator.SOURCE)
		censor_type = operation['censor-type']

		if censor_type == 'solid':
			cairo_context.set_source_rgba(*operation['replacement'])
			cairo_context.append_path(operation['path'])
			cairo_context.fill()
			return
		else:
			cairo_context.append_path(operation['path'])

		[r0, r1, r2, r3] = cairo_context.path_extents()
		[r0, r1, r2, r3] = [int(r0), int(r1), int(r2), int(r3)]
		width = r2 - r0
		height = r3 - r1
		surface = cairo.ImageSurface(cairo.Format.ARGB32, width, height)
		ccontext2 = cairo.Context(surface)
		ccontext2.set_source_surface(self._tool.get_surface(), -1 * r0, -1 * r1)
		ccontext2.paint()
		scale = self._tool.scale_factor()
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
		cairo_context.set_source_surface(bs, r0, r1)
		cairo_context.paint()

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

