# printing_manager.py
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

from gi.repository import Gtk, Gdk
import math

class DrPrintingManager():
	__gtype_name__ = 'DrPrintingManager'

	# Debug purpose only
	_AUTO_SETTINGS = False

	def __init__(self, window):
		self._window = window
		self._auto_orientation = None

	def print_pixbuf(self, pixbuf):
		"""Starts the GTK "print" dialog with a few pre-defined settings."""
		print_op = Gtk.PrintOperation()

		psetup = Gtk.PageSetup()
		if pixbuf.get_height() < pixbuf.get_width():
			self._auto_orientation = Gtk.PageOrientation.LANDSCAPE
		else:
			self._auto_orientation = Gtk.PageOrientation.PORTRAIT
		psetup.set_orientation(self._auto_orientation)
		if self._AUTO_SETTINGS:
			psetup.set_paper_size(Gtk.PaperSize('A4'))
		print_op.set_default_page_setup(psetup)

		# print_op.set_use_full_page(True) # removes margins; do i want it?

		# XXX the default preview doesn't always work, i guess it's because of
		# the sandbox, or the flatpak implementation.
		# The default preview says "evince-previewer" ???
		# I could implement a custom callback to the 'preview' signal but that
		# would be weird. And likely useless since it's only called when the
		# Gtk.PrintOperationAction given to `run` is PREVIEW???
		print_op.connect('draw-page', self._do_draw_page, pixbuf)
		print_op.connect('begin-print', self._do_begin_print, pixbuf)

		if self._AUTO_SETTINGS:
			print_op.set_export_filename("Documents/sortie.pdf")
			action_type = Gtk.PrintOperationAction.EXPORT
		else:
			action_type = Gtk.PrintOperationAction.PRINT_DIALOG
		# `res` will be Gtk.PrintOperationResult.APPLY even when "Preview" is
		# clicked, because the possible values are actually "APPLY", "CANCEL",
		# "IN_PROGRESS" and "ERROR"
		res = print_op.run(action_type, self._window)
		# I'll assume print_op continues to live enough to be used by signals.

	def _do_draw_page(self, op, print_ctx, page_num, pixbuf):
		self._show_pixbuf_on_page(print_ctx, pixbuf)

	def _do_begin_print(self, op, print_ctx, pixbuf):
		op.set_n_pages(1)
		self._show_pixbuf_on_page(print_ctx, pixbuf)

	# The typical way to use the high-level printing API is to create a
	# Gtk.PrintOperation object with Gtk.PrintOperation.new() when the user
	# selects to print. Then you set some properties on it, e.g. the page size,
	# any Gtk.PrintSettings from previous print operations, the number of pages,
	# the current page, etc.
	#
	# XXX là je ne restaure aucun PrintSettings ce qui est un problème

	def _show_pixbuf_on_page(self, print_ctx, pixbuf):
		"""Paint the (scaled) image on the page using cairo."""
		angle = self._get_delta_orientation(print_ctx)
		use_natural_ratios = (angle == 0 or angle == 180)
		scale = self._get_scale(print_ctx, pixbuf, use_natural_ratios)

		# Rotate the pixbuf
		rotated_pixbuf = pixbuf.rotate_simple(angle)

		# Set the rotated pixbuf as the context's source
		cairo_context = print_ctx.get_cairo_context()
		Gdk.cairo_set_source_pixbuf(cairo_context, rotated_pixbuf, 0, 0)

		# Scale down the context if necessary (otherwise scale may be 1.0)
		cairo_context.scale(scale, scale)

		# XXX the image should be centered in the page

		# Render the pixbuf on the page
		cairo_context.paint()

	def _get_scale(self, print_ctx, pixbuf, use_natural_ratios):
		if use_natural_ratios:
			h_ratio = print_ctx.get_height() / pixbuf.get_height()
			w_ratio = print_ctx.get_width() / pixbuf.get_width()
		else:
			h_ratio = print_ctx.get_height() / pixbuf.get_width()
			w_ratio = print_ctx.get_width() / pixbuf.get_height()

		if h_ratio < 1.0 or w_ratio < 1.0:
			scale = min(h_ratio, w_ratio)
		else:
			scale = 1.0
		return scale

	def _get_delta_orientation(self, print_ctx):
		if self._auto_orientation == Gtk.PageOrientation.PORTRAIT:
			initial_angle = 0
		else: # if self._auto_orientation == Gtk.PageOrientation.LANDSCAPE:
			initial_angle = 90

		current_orientation = print_ctx.get_page_setup().get_orientation()
		if current_orientation == Gtk.PageOrientation.PORTRAIT:
			new_angle = 0
		elif current_orientation == Gtk.PageOrientation.LANDSCAPE:
			new_angle = 90
		elif current_orientation == Gtk.PageOrientation.REVERSE_PORTRAIT:
			new_angle = 180
		else: # if current_orientation == Gtk.PageOrientation.REVERSE_LANDSCAPE:
			new_angle = 270

		delta_angle = new_angle - initial_angle
		if delta_angle < 0:
			delta_angle = delta_angle + 360
		return delta_angle

	############################################################################
################################################################################

