# saving_manager.py
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

from gi.repository import Gtk, GdkPixbuf, GLib
from .message_dialog import DrMessageDialog
from .utilities import utilities_add_filechooser_filters

ALL_SUPPORTED_FORMAT = ['jpeg', 'jpg', 'jpe', 'png', 'tiff', 'ico', 'bmp']

################################################################################

class DrSavingManager():
	__gtype_name__ = 'DrSavingManager'

	def __init__(self, window):
		self._window = window

	def save_current_image(self, is_export, to_new, selection_only, allow_alpha):
		"""All parameters are booleans. Returns a boolean (true if success)."""
		if not selection_only and not self._confirm_despite_ongoing_operation():
			return False

		if is_export:
			to_new = True

		image = self._window.get_active_image()

		if image.get_file_path() is None or to_new or selection_only:
			gfile = self._file_chooser_save()
		else:
			gfile = image.gfile

		if gfile is None:
			return False
		file_path = gfile.get_path()
		file_format = self._get_format(file_path)

		if selection_only:
			pixbuf = image.selection.get_pixbuf()
		else:
			pixbuf = image.main_pixbuf

		try:
			# Ask the user what to do concerning formats with no alpha channel
			if not allow_alpha:
				can_save_as = False
			else:
				can_save_as = not is_export
			if file_format not in ['png'] or not allow_alpha:
				replacement = self._window.gsettings.get_string('replace-alpha')
				if replacement == 'ask':
					replacement = self._ask_overwrite_alpha(allow_alpha, can_save_as)
				pixbuf = self._replace_alpha(pixbuf, replacement, image)

			# Actually save the pixbuf to the given file path
			pixbuf.savev(file_path, file_format, [None], [])

			# Update the image and the window objects
			if not is_export:
				image.gfile = gfile
				image.remember_current_state()
				image.post_save()
				self._window.set_picture_title()
		except Exception as e:
			if not is_export and str(e) == '2': # exception has been raised
				# because the user wants to save the file under an other format
				return self.saving_manager.save_current_image(False, True, False, True)
			# else the exception was raised because an actual error occured, or
			# the user clicked on "cancel" XXX that's dumb
			print(e)
			# Context: an error message
			self._window.reveal_message(_("Failed to save %s") % file_path)
			return False

		return True

	############################################################################
	# Confirmation and file-chooser dialogs ####################################

	def confirm_save_modifs(self):
		"""Return True if the image can be closed/overwritten (whether it's
		saved or not), or False otherwise (usually if the user clicked 'cancel',
		or if an error occurred)."""
		image = self._window.get_active_image()
		if image.is_saved():
			return True
		fn = image.get_file_path()
		if fn is None:
			unsaved_file_name = _("Untitled") + '.png'
			# Context: the sentence "There are unsaved modifications to %s."
			display_name = _("this picture")
		else:
			unsaved_file_name = fn.split('/')[-1]
			display_name = image.get_filename_for_display()
		dialog = DrMessageDialog(self._window)
		discard_id = dialog.set_action(_("Discard"), 'destructive-action')
		cancel_id = dialog.set_action(_("Cancel"), None)
		save_id = dialog.set_action(_("Save"), None, True)
		dialog.add_string( _("There are unsaved modifications to %s.") % display_name)
		self._window.minimap.update_minimap(True)
		image = Gtk.Image().new_from_pixbuf(self._window.minimap.mini_pixbuf)
		frame = Gtk.Frame(valign=Gtk.Align.CENTER, halign=Gtk.Align.CENTER)
		frame.add(image)
		dialog.add_widget(frame)
		result = dialog.run()
		dialog.destroy()
		if result == save_id:
			return self._window.action_save()
		elif result == discard_id:
			return True
		else: # cancel_id
			return False

	def _confirm_despite_ongoing_operation(self):
		"""Ask to the user whether or not they want to apply the operation of
		the current tool (curve, shape, transform, selection) before saving."""
		msg = None
		if self._window.get_selection_tool().selection_is_active():
			msg = _("A part of the image is selected: the pixels beneath " + \
			   "the selection will be saved with a color you might not expect!")
		elif self._window.active_tool().has_ongoing_operation():
			# Context: the user tries to save the image while previewing an
			# unapplied "transform" operation (scaling, cropping, whatever)
			msg = _("Modifications from the current tool haven't been applied.")
		if msg is None:
			return True
		dialog = DrMessageDialog(self._window)

		# If we know how to finish the ongoing operation, then let's go
		can_apply = self._window.lookup_action('apply_transform').get_enabled()
		if can_apply:
			can_unselect = self._window.active_tool().apply_to_selection
		else:
			can_unselect = self._window.lookup_action('unselect').get_enabled()
		# Otherwise the user should cancel, and apply manually

		only_2_items = not (can_apply or can_unselect)
		cancel_id = dialog.set_action(_("Cancel"), None, only_2_items)
		if only_2_items:
			save_style = 'destructive-action'
		else:
			save_style = None
		apply_id = None
		if can_apply:
			# To translators: this string should be quite short
			apply_id = dialog.set_action(_("Apply & save"), \
			                                           'suggested-action', True)
			# same label whether or not `can_unselect` too ^
		elif can_unselect:
			# To translators: this string should be quite short
			apply_id = dialog.set_action(_("Unselect & save"), \
			                                           'suggested-action', True)
		save_id = dialog.set_action(_("Save anyway"), save_style)

		dialog.add_string(msg)
		dialog.add_string(_("Do you want to save anyway?"))
		self._window.minimap.update_minimap(True)
		image = Gtk.Image().new_from_pixbuf(self._window.minimap.mini_pixbuf)
		frame = Gtk.Frame(valign=Gtk.Align.CENTER, halign=Gtk.Align.CENTER)
		frame.add(image)
		dialog.add_widget(frame)
		result = dialog.run()
		dialog.destroy()

		if result == save_id:
			return True
		elif result == cancel_id:
			return False
		elif result == apply_id:
			if can_apply:
				self._window.action_apply_transform()
			if can_unselect:
				self._window.action_unselect()
			return True
		else: # unknown id
			return False

	def _file_chooser_save(self):
		"""Opens an "save" file chooser dialog, and return a GioFile or None."""
		gfile = None
		file_chooser = Gtk.FileChooserNative.new(_("Save picture as…"),
		       self._window, Gtk.FileChooserAction.SAVE, _("Save"), _("Cancel"))
		utilities_add_filechooser_filters(file_chooser)

		images_dir = GLib.get_user_special_dir(GLib.USER_DIRECTORY_PICTURES)
		if images_dir != None: # no idea why it sometimes fails
			file_chooser.set_current_folder(images_dir)
		# Context: Untitled(.png) is the default name of a newly saved file
		default_file_name = str(_("Untitled") + '.png')
		file_chooser.set_current_name(default_file_name)

		response = file_chooser.run()
		if response == Gtk.ResponseType.ACCEPT:
			gfile = file_chooser.get_file()
		file_chooser.destroy()
		return gfile

	############################################################################
	# Pixbuf transparency ######################################################

	def _get_format(self, file_path):
		"""Build a short string which will be recognized as a file format by the
		GdkPixbuf.Pixbuf.savev method."""
		file_format = file_path.split('.')[-1]
		file_format = file_format.lower()
		if file_format in ['jpeg', 'jpg', 'jpe']:
			file_format = 'jpeg'
		elif file_format not in ALL_SUPPORTED_FORMAT:
			file_format = 'png'
		return file_format

	def _ask_overwrite_alpha(self, allow_alpha, can_save_as):
		"""Warn the user about the replacement of the alpha channel for JPG or
		BMP files, but it may quickly annoy users to see a dialog so it's an
		option. Can be used on PNG files if 'allow_alpha' is false."""
		dialog = DrMessageDialog(self._window)
		cancel_id = dialog.set_action(_("Cancel"), None)
		if can_save_as:
			save_as_id = dialog.set_action(_("Save as…"), None)
		# Context: confirm replacing transparent pixels with the selected color
		replace_id = dialog.set_action(_("Replace"), None, True)

		if allow_alpha:
			dialog.add_string(_("This file format doesn't support transparent colors."))
		if can_save_as:
			dialog.add_string(_("You can save the image as a PNG file, or " \
			                                      "replace transparency with:"))
		else:
			dialog.add_string(_("Replace transparency with:"))

		alpha_combobox = Gtk.ComboBoxText(halign=Gtk.Align.CENTER)
		alpha_combobox.append('initial', _("Default color"))
		alpha_combobox.append('white', _("White"))
		alpha_combobox.append('black', _("Black"))
		alpha_combobox.append('checkboard', _("Checkboard"))
		alpha_combobox.append('nothing', _("Nothing"))
		alpha_combobox.set_active_id('initial') # If we run the dialog, it often
		# means the active preference is 'ask', so there is no way we can set
		# the default value to something more pertinent.
		dialog.add_widget(alpha_combobox)

		result = dialog.run()
		repl = alpha_combobox.get_active_id()
		dialog.destroy()
		if result != replace_id:
			raise Exception(result)
		return repl

	def _replace_alpha(self, pixbuf, replacement, image):
		if replacement == 'nothing':
			return
		width = pixbuf.get_width()
		height = pixbuf.get_height()
		if replacement == 'white':
			pcolor1 = self._rgb_as_hexadecimal_int(255, 255, 255)
			pcolor2 = self._rgb_as_hexadecimal_int(255, 255, 255)
		elif replacement == 'initial':
			initial_rgba = image.get_initial_rgba()
			r = int(initial_rgba.red * 255)
			g = int(initial_rgba.green * 255)
			b = int(initial_rgba.blue * 255)
			# the initial color has an alpha channel but it's not pertinent, and
			# not possible anyway.
			pcolor1 = self._rgb_as_hexadecimal_int(r, g, b)
			pcolor2 = self._rgb_as_hexadecimal_int(r, g, b)
		elif replacement == 'checkboard':
			pcolor1 = self._rgb_as_hexadecimal_int(85, 85, 85)
			pcolor2 = self._rgb_as_hexadecimal_int(170, 170, 170)
		else: # if replacement == 'black':
			pcolor1 = self._rgb_as_hexadecimal_int(0, 0, 0)
			pcolor2 = self._rgb_as_hexadecimal_int(0, 0, 0)
		return pixbuf.composite_color_simple(width, height,
		                   GdkPixbuf.InterpType.TILES, 255, 8, pcolor1, pcolor2)

	def _rgb_as_hexadecimal_int(self, r, g, b):
		"""The method `GdkPixbuf.Pixbuf.composite_color_simple` wants an
		hexadecimal integer whose format is 0xaarrggbb so here are ugly binary
		operators."""
		return (r << 16) + (g << 8) + b

	############################################################################
################################################################################

