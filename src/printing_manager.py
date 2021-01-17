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

class DrPrintingManager():
	__gtype_name__ = 'DrPrintingManager'

	# Debug purpose only
	_AUTO_SETTINGS = False

	def __init__(self, window):
		self._window = window

	def print_pixbuf(self, pixbuf):
		"""Starts the GTK "print" dialog with a few pre-defined settings."""
		print_op = Gtk.PrintOperation()

		psetup = Gtk.PageSetup()
		if pixbuf.get_height() < pixbuf.get_width():
			psetup.set_orientation(Gtk.PageOrientation.LANDSCAPE)
		else:
			psetup.set_orientation(Gtk.PageOrientation.PORTRAIT)
		if self._AUTO_SETTINGS:
			psetup.set_paper_size(Gtk.PaperSize('A4'))
		print_op.set_default_page_setup(psetup)
		# print_op.set_use_full_page(True) # removes margins, do i want it?

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

	def _show_pixbuf_on_page(self, print_ctx, pixbuf):

		scale = self._get_scale(print_ctx, pixbuf)
		# XXX the image should be centered in the page
		cairo_context = print_ctx.get_cairo_context()
		Gdk.cairo_set_source_pixbuf(cairo_context, pixbuf, 0, 0)
		cairo_context.paint()
		cairo_context.scale(scale, scale)

	def _get_scale(self, print_ctx, pixbuf):
		h_ratio = print_ctx.get_height() / pixbuf.get_height()
		w_ratio = print_ctx.get_width() / pixbuf.get_width()
		if h_ratio < 1.0 or w_ratio < 1.0:
			scale = min(h_ratio, w_ratio)
		else:
			scale = 1.0
		return scale

	############################################################################
################################################################################

