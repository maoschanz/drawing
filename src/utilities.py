# utilities.py

from gi.repository import Gtk, GdkPixbuf
from .message_dialog import DrMessageDialog

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
	lumin = total/3.0
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
			color_string = _("Probably turquoise")

	else:
		color_string = _("Unknown color name")

	# print(color_string)
	return (color_string + alpha_string)

################################################################################

def utilities_save_pixbuf_to(pixbuf, fpath, window):
	"""Save pixbuf to a given path, with the file format corresponding to the
	end of the file name. Format with no support for alpha channel will be
	modified so transparent pixels get replaced by white."""
	# Build a short string which will be recognized as a file format by the
	# GdkPixbuf.Pixbuf.savev method
	file_format = fpath.split('.')[-1]
	if file_format in ['jpeg', 'jpg', 'jpe']:
		file_format = 'jpeg'
	elif file_format not in ['jpeg', 'jpg', 'jpe', 'png', 'tiff', 'ico', 'bmp']:
		file_format = 'png'
	# Ask the user what to do concerning formats with no alpha channel
	if file_format not in ['png']:
		replacement = window._settings.get_string('replace-alpha')
		if replacement == 'ask':
			replacement = _ask_overwrite_alpha(window)
		_replace_alpha(pixbuf, replacement)
	# Actually save the pixbuf to the given file path
	pixbuf.savev(fpath, file_format, [None], [])

def _replace_alpha(pixbuf, replacement):
	if replacement == 'nothing':
		return
	width = pixbuf.get_width()
	height = pixbuf.get_height()
	if replacement == 'white':
		pcolor1 = _rgb_as_hexadecimal_int(255, 255, 255)
		pcolor2 = _rgb_as_hexadecimal_int(255, 255, 255)
	elif replacement == 'checkboard':
		pcolor1 = _rgb_as_hexadecimal_int(85, 85, 85)
		pcolor2 = _rgb_as_hexadecimal_int(170, 170, 170)
	else: # if replacement == 'black':
		pcolor1 = _rgb_as_hexadecimal_int(0, 0, 0)
		pcolor2 = _rgb_as_hexadecimal_int(0, 0, 0)
	pixbuf = pixbuf.composite_color_simple(width, height,
	                       GdkPixbuf.InterpType.TILES, 255, 8, pcolor1, pcolor2)

def _rgb_as_hexadecimal_int(r, g, b):
	"""The method GdkPixbuf.Pixbuf.composite_color_simple wants an hexadecimal
	integer whose format is 0xaarrggbb so here are ugly binary operators."""
	return (r << 16) + (g << 8) + b

def _ask_overwrite_alpha(window):
	"""This method is not used for now. The point is to warn the user about the
	replacement of the alpha channel for JPG or BMP files, but it might annoy
	users very quickly to see a dialog."""
	dialog = DrMessageDialog(window)
	cancel_id = dialog.set_action(_("Cancel"), None, False)
	continue_id = dialog.set_action(_("Save"), None, True)
	dialog.add_string(_("This file format doesn't support transparent colors."))

	dialog.add_string(_("Replace transparency with:") )
	alpha_combobox = Gtk.ComboBoxText(halign=Gtk.Align.CENTER)
	dialog.add_widget(alpha_combobox)
	alpha_combobox.append('white', _("White"))
	alpha_combobox.append('black', _("Black"))
	alpha_combobox.append('checkboard', _("Checkboard"))
	alpha_combobox.append('nothing', _("Nothing"))
	alpha_combobox.set_active_id('white') # If we run the dialog, it means the
	# active preference IS 'ask', so there is no way we can set the value to
	# something pertinent.

	result = dialog.run()
	repl = alpha_combobox.get_active_id()
	dialog.destroy()
	if result != continue_id:
		raise Exception("User refused to save as %s" % file_format)
	return repl

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
		_add_spinbutton_icon(spinbutton, 'unit-pixels-symbolic', _("pixels"))
	elif unit == '%':
		_add_spinbutton_icon(spinbutton, 'unit-percents-symbolic', _("percents"))

def _add_spinbutton_icon(spinbutton, icon, tooltip):
	p = Gtk.EntryIconPosition.SECONDARY
	spinbutton.set_icon_from_icon_name(p, icon)
	spinbutton.set_icon_tooltip_text(p, tooltip)
	spinbutton.set_icon_sensitive(p, False)

################################################################################

