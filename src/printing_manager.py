# printing_manager.py
#
# Copyright 2020 Romain F. T.
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

	def __init__(self, window):
		self._window = window

	def print_pixbuf(self, pixbuf):
		print_op = Gtk.PrintOperation() # ça a des signaux pour des widgets
		# custom ça, c'est vraiment le portal flatpak ?

		psetup = Gtk.PageSetup()
		if pixbuf.get_height() < pixbuf.get_width():
			# XXX seulement si l'image est plus large que la largeur du format
			# portrait ? osef en vrai, flemme
			psetup.set_orientation(Gtk.PageOrientation.LANDSCAPE)
		else:
			psetup.set_orientation(Gtk.PageOrientation.PORTRAIT)
		print_op.set_default_page_setup(psetup)
		# print_op.set_use_full_page(True) # ?

		# FIXME the default preview doesn't always work, i guess it's because of
		# the sandbox, or the flatpak implementation.
		# The default preview says "evince-previewer" ???
		# I could implement a custom callback to the 'preview' signal but that
		# would be weird. And likely useless since it's not called at all?????
		print_op.connect('draw-page', self._do_draw_page, pixbuf)
		print_op.connect('begin-print', self._do_begin_print, pixbuf)

		res = print_op.run(Gtk.PrintOperationAction.PRINT_DIALOG, self._window)
		# si on apply réellement (du moins avec l'impression vers pdf), ça
		# begin-print puis ça draw-page avant de retourner du run
		print(res) # pourquoi le résultat est Gtk.PrintOperationResult.APPLY
		# même quand on clique sur "Aperçu" ??? XXX
		# I assume print_op continues to live enough to be used by signals.

	def _do_draw_page(self, op, print_ctx, page_num, pixbuf):
		self._show_pixbuf_on_page(print_ctx, pixbuf)

	def _do_begin_print(self, op, print_ctx, pixbuf):
		op.set_n_pages(1)
		self._show_pixbuf_on_page(print_ctx, pixbuf)

	def _show_pixbuf_on_page(self, print_ctx, pixbuf):
		# TODO if it's too big for one page ? la technique est de scale down
		scale = 1.0
		print(scale)

		cairo_context = print_ctx.get_cairo_context()
		cairo_context.scale(scale, scale)
		Gdk.cairo_set_source_pixbuf(cairo_context, pixbuf, 0, 0)
		cairo_context.paint()

	############################################################################
################################################################################

