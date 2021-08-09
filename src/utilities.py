# utilities.py
#
# Copyright 2018-2021 Romain F. T.
#
# GPL 3

from gi.repository import Gtk, Gio

################################################################################

def utilities_get_rgba_name(red, green, blue, alpha):
	"""To improve accessibility, it is useful to display the name of the colors.
	Sadly, it's a mess to implement, and it's quite approximative."""
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

def utilities_add_filechooser_filters(dialog):
	"""Add file filters for images to file chooser dialogs."""
	allPictures = Gtk.FileFilter()
	allPictures.set_name(_("All pictures"))
	allPictures.add_mime_type('image/png')
	allPictures.add_mime_type('image/jpeg')
	allPictures.add_mime_type('image/bmp')

	pngPictures = Gtk.FileFilter()
	pngPictures.set_name(_("PNG images"))
	pngPictures.add_mime_type('image/png')

	jpegPictures = Gtk.FileFilter()
	jpegPictures.set_name(_("JPEG images"))
	jpegPictures.add_mime_type('image/jpeg')

	bmpPictures = Gtk.FileFilter()
	bmpPictures.set_name(_("BMP images"))
	bmpPictures.add_mime_type('image/bmp')

	dialog.add_filter(allPictures)
	dialog.add_filter(pngPictures)
	dialog.add_filter(jpegPictures)
	dialog.add_filter(bmpPictures)

################################################################################

def utilities_add_unit_to_spinbtn(spinbutton, width_chars, unit):
	spinbutton.set_width_chars(width_chars + 3)
	if unit == 'px':
		# To translators: it's a measure unit, it appears in tooltips over
		# numerical inputs
		_add_spinbutton_icon(spinbutton, 'unit-pixels-symbolic', _("pixels"))
	elif unit == '%':
		# To translators: it appears in tooltips over numerical inputs
		_add_spinbutton_icon(spinbutton, 'unit-percents-symbolic', _("percents"))
	elif unit == '°':
		# To translators: it's the angle measure unit, it appears in a tooltip
		# over a numerical input
		_add_spinbutton_icon(spinbutton, 'unit-degrees-symbolic', _("degrees"))

def _add_spinbutton_icon(spinbutton, icon, tooltip):
	p = Gtk.EntryIconPosition.SECONDARY
	spinbutton.set_icon_from_icon_name(p, icon)
	spinbutton.set_icon_tooltip_text(p, tooltip)
	spinbutton.set_icon_sensitive(p, False)

################################################################################

def utilities_gfile_is_image(gfile, error_msg=""):
	try:
		infos = gfile.query_info('standard::*', Gio.FileQueryInfoFlags.NONE, None)
		if 'image/' in infos.get_content_type():
			# The exact file format of the image isn't validated here because i
			# can't assume what gdkpixbuf is able to read (it's modular, and it
			# evolves). An InvalidFileFormatException will be raised by DrImage
			# if the file can't be loaded.
			return True, error_msg
		else:
			error_msg = error_msg + _("%s isn't an image.") % gfile.get_path()
	except Exception as err:
		error_msg = error_msg + err.message
	return False, error_msg

class InvalidFileFormatException(Exception):
	def __init__(self, initial_message, fpath):
		self.message = initial_message
		cpt = 0
		with open(fpath, 'rb') as f:
			riff_bytes = f.read(4)
			size_bytes = f.read(4)
			webp_bytes = f.read(4)
			if riff_bytes == b'RIFF' and webp_bytes == b'WEBP':
				msg = _("Sorry, WEBP images can't be loaded by this app.") + " 😢 "
				if fpath[-5:] != '.webp':
					# Context: an error message, %s is a file path
					msg = msg + _("Despite its name, %s is a WEBP file.") % fpath
				self.message = msg
		super().__init__(self.message)
	# This exception is meant to be raised when a file is detected as an image
	# by Gio (see utility function above) BUT can't be loaded into a GdkPixbuf.
	# It usually means the file is corrupted, or has a deceptive name (for
	# example "xxx.jpeg" despite being a text file), or is just an image format
	# not supported by the GdkPixbuf version installed by the user.

################################################################################

