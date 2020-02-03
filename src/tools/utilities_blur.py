# blurring.py
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

import cairo, threading
from datetime import datetime # Not actually needed, just to measure perfs XXX

class BlurType():
	INVALID = -1
	AUTO = 0
	PX_BOX = 1
	PX_HORIZONTAL = 2
	PX_VERTICAL = 3
	PX_BOX_MULTI = 4
	CAIRO_BOX = 5
	CAIRO_HORIZONTAL = 6
	CAIRO_VERTICAL = 7

################################################################################

def utilities_fast_blur(surface, radius, algotype):
	"""This is the 'official' method to access the blur algorithms. The last
	argument is an integer corresponding to the BlurType enumeration."""
	radius = int(radius)
	if radius < 1:
		return

	if algotype == BlurType.INVALID:
		return
	elif algotype == BlurType.AUTO:
		algotype = BlurType.PX_BOX
		# if radius > 6:
		# 	algotype = BlurType.PX_BOX
		# else:
		# 	algotype = BlurType.CAIRO_BOX

	w = surface.get_width()
	h = surface.get_height()
	channels = 4 # ARGB
	if radius > w - 1 or radius > h - 1:
		return

	# this code a modified version of this https://github.com/elementary/granite/blob/14e3aaa216b61f7e63762214c0b36ee97fa7c52b/lib/Drawing/BufferSurface.vala#L230
	# the main differences (aside of the language) is the poor attempt to use
	# multithreading (i'm quite sure the access to buffers are not safe at all).
	# The 2 phases of the algo have been separated to allow directional blur.
	original = cairo.ImageSurface(cairo.Format.ARGB32, w, h)
	cairo_context = cairo.Context(original)
	# cairo_context.set_operator(cairo.Operator.SOURCE)
	cairo_context.set_source_surface(surface, 0, 0)
	cairo_context.paint()
	original.flush()
	pixels = original.get_data()

	buffer0 = [None] * (w * h * channels)
	vmin = [None] * max(w, h)
	vmax = [None] * max(w, h)
	div = 2 * radius + 1
	dv = [None] * (256 * div)
	for i in range(0, len(dv)):
		dv[i] = int(i / div)

	iterations = 1
	while iterations > 0:
		iterations = iterations - 1
		time0 = datetime.now()
		print('begin fast blur, using algo n°', algotype)
		if algotype == BlurType.PX_HORIZONTAL:
			_fast_blur_1st_phase(w, h, channels, radius, pixels, buffer0, vmin, vmax, dv)
			for i in range(0, len(buffer0)):
				pixels[i] = buffer0[i] # XXX useful?
		elif algotype == BlurType.PX_VERTICAL:
			for i in range(0, len(pixels)):
				buffer0[i] = pixels[i] # XXX useful?
			_fast_blur_2nd_phase(w, h, channels, radius, pixels, buffer0, vmin, vmax, dv)
		elif algotype == BlurType.PX_BOX:
			_fast_blur_1st_phase(w, h, channels, radius, pixels, buffer0, vmin, vmax, dv)
			# print('end of the 1st phase…', datetime.now() - time0)
			_fast_blur_2nd_phase(w, h, channels, radius, pixels, buffer0, vmin, vmax, dv)

		elif algotype == BlurType.PX_BOX_MULTI:
			full_buff = _fast_blur_1st_phase_multi(w, h, channels, radius, \
			                                             pixels, vmin, vmax, dv)
			# print('end of the 1st phase…', datetime.now() - time0)
			_fast_blur_2nd_phase(w, h, channels, radius, pixels, full_buff, vmin, vmax, dv)

		elif algotype == BlurType.CAIRO_BOX:
			original = _cairo_blur(radius, original)
		elif algotype == BlurType.CAIRO_HORIZONTAL:
			original = _cairo_blur_h(radius, original)
		elif algotype == BlurType.CAIRO_VERTICAL:
			original = _cairo_blur_v(radius, original)
		else:
			pass # pas encore implémenté

		time1 = datetime.now()
		print('fast blur ended, total time:', time1 - time0)
	return original

################################################################################
# this code a modified version of a naïve approach to box blur, copied from
# here: https://github.com/elementary/granite/blob/14e3aaa216b61f7e63762214c0b36ee97fa7c52b/lib/Drawing/BufferSurface.vala#L230
# the main differences (aside of the language) is the poor attempt to use
# multithreading (i'm quite sure the access to buffers are not safe at all)
# during the first phase. Multithreading of the second phase has not been tried
# since this multithreaded version is slower than _fast_blur_1st_phase

def _fast_blur_1st_phase_multi(w, h, channels, radius, pixels, vmin, vmax, dv):
	NB_THREADS = 4
	t1 = [None] * NB_THREADS
	full_buffer = []
	buffers = []
	y_end = 0
	for x in range(0, w):
		vmin[x] = min(x + radius + 1, w - 1)
		vmax[x] = max(x - radius, 0)
	for t in range(0, NB_THREADS):
		y_start = y_end
		if t == NB_THREADS - 1:
			y_end = h
		else:
			y_end = y_start + int(h / NB_THREADS)
		buff_size = w * (y_end - y_start) * channels
		buff = [0] * buff_size
		buffers.append(buff)
		t1[t] = threading.Thread(target=_blur_rows3, args=(x, y_start, y_end, \
		                     w, channels, radius, pixels, buff, vmin, vmax, dv))
	for t in range(0, NB_THREADS):
		t1[t].start()
	for t in range(0, NB_THREADS):
		t1[t].join()
		full_buffer += buffers[t]
	return full_buffer

def _blur_rows3(x, y0, y1, w, channels, radius, pixels, buff0, vmin, vmax, dv):
	# print('row thread with', y0, y1, '(begin)')
	diff = y0 * w * channels
	for y in range(y0, y1):
		cur_pixel = y * w * channels
		asum = radius * pixels[cur_pixel + 0]
		rsum = radius * pixels[cur_pixel + 1]
		gsum = radius * pixels[cur_pixel + 2]
		bsum = radius * pixels[cur_pixel + 3]
		for i in range(0, radius+1):
			asum += pixels[cur_pixel + 0]
			rsum += pixels[cur_pixel + 1]
			gsum += pixels[cur_pixel + 2]
			bsum += pixels[cur_pixel + 3]
			cur_pixel += channels
		cur_pixel = y * w * channels - diff
		for x in range(0, w):
			p1 = (y * w + vmin[x]) * channels
			p2 = (y * w + vmax[x]) * channels
			buff0[cur_pixel + 0] = dv[asum]
			buff0[cur_pixel + 1] = dv[rsum]
			buff0[cur_pixel + 2] = dv[gsum]
			buff0[cur_pixel + 3] = dv[bsum]
			asum += pixels[p1 + 0] - pixels[p2 + 0]
			rsum += pixels[p1 + 1] - pixels[p2 + 1]
			gsum += pixels[p1 + 2] - pixels[p2 + 2]
			bsum += pixels[p1 + 3] - pixels[p2 + 3]
			cur_pixel += channels
	# print('row thread with', y0, y1, '(end)')

################################################################################
# this code a modified version of a naïve approach to box blur, copied from
# here: https://github.com/elementary/granite/blob/14e3aaa216b61f7e63762214c0b36ee97fa7c52b/lib/Drawing/BufferSurface.vala#L230
# The 2 phases of the algo have been separated to allow directional blur.

def _fast_blur_1st_phase(w, h, channels, radius, pixels, buff0, vmin, vmax, dv):
	for x in range(0, w):
		vmin[x] = min(x + radius + 1, w - 1)
		vmax[x] = max(x - radius, 0)
	for y in range(0, h):
		cur_pixel = y * w * channels
		asum = radius * pixels[cur_pixel + 0]
		rsum = radius * pixels[cur_pixel + 1]
		gsum = radius * pixels[cur_pixel + 2]
		bsum = radius * pixels[cur_pixel + 3]
		for i in range(0, radius+1):
			asum += pixels[cur_pixel + 0]
			rsum += pixels[cur_pixel + 1]
			gsum += pixels[cur_pixel + 2]
			bsum += pixels[cur_pixel + 3]
			cur_pixel += channels
		cur_pixel = y * w * channels
		for x in range(0, w):
			p1 = (y * w + vmin[x]) * channels
			p2 = (y * w + vmax[x]) * channels
			buff0[cur_pixel + 0] = dv[asum]
			buff0[cur_pixel + 1] = dv[rsum]
			buff0[cur_pixel + 2] = dv[gsum]
			buff0[cur_pixel + 3] = dv[bsum]
			asum += pixels[p1 + 0] - pixels[p2 + 0]
			rsum += pixels[p1 + 1] - pixels[p2 + 1]
			gsum += pixels[p1 + 2] - pixels[p2 + 2]
			bsum += pixels[p1 + 3] - pixels[p2 + 3]
			cur_pixel += channels

def _fast_blur_2nd_phase(w, h, channels, radius, pixels, buff0, vmin, vmax, dv):
	for y in range(0, h):
		vmin[y] = min(y + radius + 1, h - 1) * w
		vmax[y] = max (y - radius, 0) * w
	for x in range(0, w):
		cur_pixel = x * channels
		asum = radius * buff0[cur_pixel + 0]
		rsum = radius * buff0[cur_pixel + 1]
		gsum = radius * buff0[cur_pixel + 2]
		bsum = radius * buff0[cur_pixel + 3]
		for i in range(0, radius+1):
			asum += buff0[cur_pixel + 0]
			rsum += buff0[cur_pixel + 1]
			gsum += buff0[cur_pixel + 2]
			bsum += buff0[cur_pixel + 3]
			cur_pixel += w * channels
		cur_pixel = x * channels
		for y in range(0, h):
			p1 = (x + vmin[y]) * channels
			p2 = (x + vmax[y]) * channels
			pixels[cur_pixel + 0] = dv[asum]
			pixels[cur_pixel + 1] = dv[rsum]
			pixels[cur_pixel + 2] = dv[gsum]
			pixels[cur_pixel + 3] = dv[bsum]
			asum += buff0[p1 + 0] - buff0[p2 + 0]
			rsum += buff0[p1 + 1] - buff0[p2 + 1]
			gsum += buff0[p1 + 2] - buff0[p2 + 2]
			bsum += buff0[p1 + 3] - buff0[p2 + 3]
			cur_pixel += w * channels

################################################################################
# Failed attempt to produce a blurred image using cairo. I mean ok, the image is
# blurred, and with amazing performances, but the quality is not convincing and
# the result when the area has (semi-)transparency actually sucks.

def _cairo_blur(radius, surface):
	for i in range(3): # XXX dégueulasse mdrrr
		surface = _cairo_directional_blur(surface, radius, surface, True)
		surface = _cairo_directional_blur(surface, radius, surface, False)
	return surface

def _cairo_blur_h(radius, surface):
	for i in range(3): # XXX dégueulasse mdrrr
		surface = _cairo_directional_blur(surface, radius, surface, False)
	return surface

def _cairo_blur_v(radius, surface):
	for i in range(3): # XXX dégueulasse mdrrr
		surface = _cairo_directional_blur(surface, radius, surface, True)
	return surface

def _cairo_directional_blur(source_surf, radius, target_surf, is_vertical):
	cairo_context = cairo.Context(target_surf)
	step = max(1, int(radius / 6))
	alpha = step / radius
	# XXX l'alpha n'est pas correct
	for i in range(-1 * radius, radius, step):
		if is_vertical:
			cairo_context.set_source_surface(source_surf, 0, i)
		else:
			cairo_context.set_source_surface(source_surf, i, 0)
		cairo_context.paint_with_alpha(alpha)
	target_surf.flush()
	return target_surf

################################################################################

