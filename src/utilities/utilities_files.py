# utilities.py
#
# Copyright 2018-2021 Romain F. T.
#
# GPL 3

from gi.repository import Gtk, Gio

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

