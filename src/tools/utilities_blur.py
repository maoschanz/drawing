# utilities_blur.py
#
# Copyright 2018-2021 Romain F. T.
#
# GPL 3

import cairo, threading
# from datetime import datetime # Not actually needed, just to measure perfs

class BlurType(int):
	INVALID = -1
	AUTO = 0
	PX_BOX = 1
	PX_BOX_MULTI = 2
	CAIRO_REPAINTS = 3
	TILES = 4

class BlurDirection(int):
	INVALID = -1
	BOTH = 0
	HORIZONTAL = 1
	VERTICAL = 2

################################################################################

def utilities_blur_surface(surface, radius, blur_type, blur_direction):
	"""This is the 'official' method to access the blur algorithms.
	The third argument is an integer corresponding to the BlurType enumeration.
	The 4th one is an integer corresponding to the BlurDirection enumeration."""
	radius = int(radius)
	if radius < 1:
		return surface
	blurred_surface = None
	# time0 = datetime.now()
	# print('blurring begins, using algo ', blur_type, '-', blur_direction)

	if blur_type == BlurType.INVALID:
		return surface
	elif blur_type == BlurType.AUTO:
		blur_type = BlurType.PX_BOX
		# XXX c'est nul ça mdr, mais bon c'est peu utilisé

	if blur_type == BlurType.PX_BOX:
		blurred_surface = _generic_px_box_blur(surface, radius, blur_direction)
	elif blur_type == BlurType.PX_BOX_MULTI:
		blurred_surface = _generic_multi_threaded_blur(surface, radius, blur_direction)
	elif blur_type == BlurType.CAIRO_REPAINTS:
		blurred_surface = _generic_cairo_blur(surface, radius, blur_direction)
	elif blur_type == BlurType.TILES:
		blurred_surface = _generic_tiled_blur(surface, radius, blur_direction)

	# time1 = datetime.now()
	# print('blurring ended, total time:', time1 - time0)
	return blurred_surface

################################################################################
# BlurType.PX_BOX ##############################################################

def _generic_px_box_blur(surface, radius, blur_direction):
	w = surface.get_width()
	h = surface.get_height()
	channels = 4 # ARGB
	if radius > w - 1 or radius > h - 1:
		return surface

	# this code a modified version of this https://github.com/elementary/granite/blob/14e3aaa216b61f7e63762214c0b36ee97fa7c52b/lib/Drawing/BufferSurface.vala#L230
	# the main differences (aside of the language) is the poor attempt to use
	# multithreading (i'm quite sure the access to buffers are not safe at all).
	# The 2 phases of the algo have been separated to allow directional blur.
	original = cairo.ImageSurface(cairo.Format.ARGB32, w, h)
	cairo_context = cairo.Context(original)
	# cairo_context.set_operator(cairo.Operator.SOURCE)
	cairo_context.set_source_surface(surface, 0, 0)
	cairo_context.paint() # XXX is this copy useful?
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
		if blur_direction == BlurDirection.VERTICAL:
			for i in range(0, len(pixels)):
				buffer0[i] = pixels[i]
		else:
			_box_blur_1st_phase(w, h, channels, radius, pixels, buffer0, vmin, vmax, dv)
		# print('end of the 1st phase…', datetime.now() - time0)
		if blur_direction == BlurDirection.HORIZONTAL:
			for i in range(0, len(buffer0)):
				pixels[i] = buffer0[i]
		else:
			_box_blur_2nd_phase(w, h, channels, radius, pixels, buffer0, vmin, vmax, dv)
	return original

# this code a modified version of a naïve approach to box blur, copied from
# here: https://github.com/elementary/granite/blob/14e3aaa216b61f7e63762214c0b36ee97fa7c52b/lib/Drawing/BufferSurface.vala#L230
# The 2 phases of the algo have been separated to allow directional blur.

def _box_blur_1st_phase(w, h, channels, radius, pixels, buff0, vmin, vmax, dv):
	"""Horizontal blurring"""
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

def _box_blur_2nd_phase(w, h, channels, radius, pixels, buff0, vmin, vmax, dv):
	"""Vertical blurring"""
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
# BlurType.PX_BOX_MULTI ########################################################

def _generic_multi_threaded_blur(surface, radius, blur_direction):
	"""Experimental multi-threaded blur. The parameter `blur_direction` will be
	ignored (it always blurs in both directions)."""
	w = surface.get_width()
	h = surface.get_height()
	channels = 4 # ARGB
	if radius > w - 1 or radius > h - 1:
		return

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

	full_buff = _box_blur_1st_phase_multi(w, h, channels, radius, pixels, vmin, vmax, dv)
	# print('end of the 1st phase…', datetime.now() - time0)
	_box_blur_2nd_phase(w, h, channels, radius, pixels, full_buff, vmin, vmax, dv)

	return original

# this code a modified version of a naïve approach to box blur, copied from
# here: https://github.com/elementary/granite/blob/14e3aaa216b61f7e63762214c0b36ee97fa7c52b/lib/Drawing/BufferSurface.vala#L230
# the main differences (aside of the language) is the poor attempt to use
# multithreading (i'm quite sure the access to buffers are not safe at all)
# during the first phase. Multithreading of the second phase has not even been
# tried because this multithreaded version is slower than _box_blur_1st_phase

def _box_blur_1st_phase_multi(w, h, channels, radius, pixels, vmin, vmax, dv):
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
# BlurType.CAIRO_REPAINTS ######################################################

def _generic_cairo_blur(surface, radius, blur_direction):
	if blur_direction == BlurDirection.HORIZONTAL:
		surface = _cairo_directional_blur(surface, radius, False)
	elif blur_direction == BlurDirection.VERTICAL:
		surface = _cairo_directional_blur(surface, radius, True)
	else:
		# XXX with some big radius, it's visible that it's just a sequence of
		# 2 directional blurs instead of an actual algorithm
		surface = _cairo_directional_blur(surface, radius, True)
		surface = _cairo_directional_blur(surface, radius, False)
	return surface

# Weird attempt to produce a blurred image using cairo. I mean ok, the image is
# blurred, and with amazing performances, but the quality is not convincing and
# the result when the area has (semi-)transparency really sucks.

def _cairo_directional_blur(surface, radius, is_vertical):
	cairo_context = cairo.Context(surface)
	if radius < 10:
		step = 1
		alpha = min(0.9, step / radius)
	elif radius < 15:
		step = 1
		alpha = min(0.9, (0.5 + step) / radius)
	else:
		step = int(radius / 6) # why 6? mystery
		# cette optimisation donne de légers glitchs aux grands radius, qui ne
		# sont de toutes manières pas beaux car on voit en partie à travers
		alpha = min(0.9, (1 + step) / radius)
	for i in range(-1 * radius, radius, step):
		if is_vertical:
			cairo_context.set_source_surface(surface, 0, i)
		else:
			cairo_context.set_source_surface(surface, i, 0)
		cairo_context.paint_with_alpha(alpha)
	surface.flush()
	return surface

################################################################################
# BlurType.TILES ###############################################################

def _generic_tiled_blur(surface, radius, blur_direction):
	if blur_direction == BlurDirection.HORIZONTAL:
		tile_width = radius
		tile_height = 1
	elif blur_direction == BlurDirection.VERTICAL:
		tile_width = 1
		tile_height = radius
	else:
		tile_width = radius
		tile_height = radius
	return _get_tiled_surface(surface, tile_width, tile_height)

def _get_tiled_surface(surface, tile_width, tile_height):
	w = surface.get_width()
	h = surface.get_height()
	channels = 4 # ARGB
	pixels = surface.get_data()
	pixel_max = w * h * channels

	for x in range(0, w, tile_width):
		for y in range(0, h, tile_height):
			current_pixel = (x + (w * y)) * channels
			if current_pixel >= pixel_max:
				continue
			tile_b = pixels[current_pixel + 0]
			tile_g = pixels[current_pixel + 1]
			tile_r = pixels[current_pixel + 2]
			tile_a = pixels[current_pixel + 3]
			for tx in range(0, tile_width):
				for ty in range(0, tile_height):
					current_pixel = ((x + tx) + (w * (y + ty))) * channels
					if current_pixel >= pixel_max:
						continue
					if current_pixel >= (w * (y + ty + 1)) * channels:
						# the current tile is out of the surface, this guard
						# clause avoids corrupting the next tile
						continue
					pixels[current_pixel + 0] = tile_b
					pixels[current_pixel + 1] = tile_g
					pixels[current_pixel + 2] = tile_r
					pixels[current_pixel + 3] = tile_a
			# end of one tile
	# end of the "for each tile"
	return surface

################################################################################

