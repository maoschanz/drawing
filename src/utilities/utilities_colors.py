# Licensed under GPL3 https://github.com/maoschanz/drawing/blob/master/LICENSE

from gi.repository import Gdk

from .utilities_paths import utilities_get_rgba_for_xy

################################################################################

def utilities_gdk_rgba_to_color_array(gdk_rgba):
	"""Convert a Gdk.RGBA to an array of values intended to be used directly by
	cairo. Thus the value of alpha between 0 and 1, despite the 3 other values
	being integers between 0 and 255."""
	r = int(255 * gdk_rgba.red)
	g = int(255 * gdk_rgba.green)
	b = int(255 * gdk_rgba.blue)
	return [r, g, b, gdk_rgba.alpha]

def utilities_gdk_rgba_to_normalized_array(gdk_rgba):
	"""Convert a Gdk.RGBA to an array of values between 0 and 1."""
	return [gdk_rgba.red, gdk_rgba.green, gdk_rgba.blue, gdk_rgba.alpha]

def utilities_color_array_to_gdk_rgba(r, g, b, a):
	"""Convert an array of values (as used by cairo) to a Gdk.RGBA object. The
	values should be integers between 0 and 255, except alpha."""
	if a > 1.0:
		raise Exception("Incorrect value for alpha")
	return Gdk.RGBA(red=r / 255, green=g / 255, blue=b / 255, alpha=a)

################################################################################

def utilities_rgba_to_hexadecimal(r, g, b, a):
	"""Methods such as `GdkPixbuf.Pixbuf.fill` wants an hexadecimal integer
	whose format is 0xrrggbbaa so here are ugly binary operators.
	All four values (even alpha!) must be between 0 and 255."""
	r, g, b, a = int(r), int(g), int(b), int(a)
	return (((((r << 8) + g) << 8) + b) << 8) + a

def utilities_rgb_to_hexadecimal(r, g, b):
	"""Methods such as `GdkPixbuf.Pixbuf.composite_color_simple` want an
	hexadecimal integer whose format is 0xaarrggbb so here are ugly binary
	operators."""
	return (r << 16) + (g << 8) + b

def utilities_gdk_rgba_to_hexadecimal(gdk_rgba):
	"""Returns a displayable string of the hexadecimal code corresponding to a
	Gdk.RGBA object."""
	r = int(255 * gdk_rgba.red)
	g = int(255 * gdk_rgba.green)
	b = int(255 * gdk_rgba.blue)
	hexa_raw = hex(utilities_rgb_to_hexadecimal(r, g, b))
	hexa_string = str(hexa_raw)[2:]
	hexa_string = "0" * (6 - len(hexa_string)) + hexa_string
	return "#" + hexa_string

################################################################################

def utilities_gdk_rgba_from_xy(surface, event_x, event_y):
	rgba_vals = utilities_get_rgba_for_xy(surface, event_x, event_y)
	if rgba_vals is None:
		return # event outside of the surface
	rgba_vals = [*rgba_vals]
	rgba_vals[3] /= 255 # alpha has to be between 0 and 1
	return utilities_color_array_to_gdk_rgba(*rgba_vals)

################################################################################

def utilities_get_rgba_name(gdk_rgba):
	"""To improve accessibility, it is useful to display the name of the colors.
	Sadly, it's a mess to implement, and it's quite approximative."""
	[red, green, blue, alpha] = utilities_gdk_rgba_to_normalized_array(gdk_rgba)
	color_string = ""
	alpha_string = ""
	if alpha == 0.0:
		return _("Transparent")
	elif alpha < 1.0:
		alpha_string = ' - ' + _("%s%% transparent") % int(100 - alpha * 100)

	total = red + green + blue
	orange_coef = 0.0
	lumin = total / 3.0
	# print(lumin)
	if green != 0:
		orange_coef = (red/green) * lumin

	if total != 0:
		rgb_percents = [red/total, green/total, blue/total]
	else:
		rgb_percents = [0.333, 0.333, 0.333]
	# print(rgb_percents)

	grey_coef_r = rgb_percents[0] * lumin / 3
	grey_coef_g = rgb_percents[1] * lumin / 3
	grey_coef_b = rgb_percents[2] * lumin / 3
	is_grey = abs(grey_coef_r - grey_coef_g) < 0.01
	is_grey = is_grey and abs(grey_coef_g - grey_coef_b) < 0.01
	is_grey = is_grey and abs(grey_coef_b - grey_coef_r) < 0.01

	if is_grey:
		if lumin > 0.9:
			color_string = _("White")
		elif lumin < 0.1:
			color_string = _("Black")
		else:
			color_string = _("Grey")

	elif rgb_percents[0] > 0.5 and rgb_percents[1] > 0.2 and rgb_percents[1] < 0.4:
		if orange_coef > 0.87:
			color_string = _("Orange")
		else:
			color_string = _("Brown")

	elif rgb_percents[0] > 0.4 and rgb_percents[1] < 0.3 and rgb_percents[2] < 0.3:
		if lumin < 0.7 and rgb_percents[0] < 0.7:
			# Context: the name of the current color is provided as a tooltip to
			# help users with color blindness, but some color names don't have a
			# clear definition. Here, the app thinks it's probably brown.
			color_string = _("Probably brown")
		else:
			color_string = _("Red")
	elif rgb_percents[1] > 0.4 and rgb_percents[0] < 0.4 and rgb_percents[2] < 0.4:
		color_string = _("Green")
	elif rgb_percents[2] > 0.4 and rgb_percents[0] < 0.3 and rgb_percents[1] < 0.4:
		color_string = _("Blue")

	elif rgb_percents[0] > 0.3 and rgb_percents[1] > 0.3 and rgb_percents[2] < 0.3:
		if rgb_percents[1] < 0.4:
			color_string = _("Probably brown")
		else:
			color_string = _("Yellow")
	elif rgb_percents[0] > 0.3 and rgb_percents[2] > 0.3 and rgb_percents[1] < 0.3:
		if lumin > 0.6 and rgb_percents[1] < 0.1:
			color_string = _("Magenta")
		else:
			color_string = _("Purple")
	elif rgb_percents[1] > 0.3 and rgb_percents[2] > 0.3 and rgb_percents[0] < 0.2:
		if lumin > 0.7:
			color_string = _("Cyan")
		else:
			# Context: the name of the current color is provided as a tooltip to
			# help users with color blindness, but some color names don't have a
			# clear definition. Here, the app thinks it's probably teal.
			# You can translate "teal" with the name of approaching color, like
			# turquoise or green-blue.
			color_string = _("Probably teal")

	else:
		# Context: the name of the current color is provided as a tooltip to
		# help users with color blindness, but some color names don't have a
		# clear definition. Here, the app can't find a corresponding color name.
		color_string = _("Unknown color name")

	# print(color_string)
	return (color_string + alpha_string)

################################################################################

