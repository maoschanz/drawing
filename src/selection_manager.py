# selection_manager.py
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

import cairo
from gi.repository import Gtk, Gdk, GdkPixbuf

class NoSelectionPixbufException(Exception):
	def __init__(self, *args):
		# Context: an error message
		super().__init__(_("The selection pixbuf is empty."))

class NoSelectionPathException(Exception):
	def __init__(self, *args):
		super().__init__(_("The selection path is empty."))

################################################################################

class DrSelectionManager():
	__gtype_name__ = 'DrSelectionManager'

	def __init__(self, image):
		self.image = image
		self.init_pixbuf()
		self.reset_future_data()

		builder = Gtk.Builder.new_from_resource( \
		                '/com/github/maoschanz/drawing/ui/selection-manager.ui')
		menu_r = builder.get_object('inactive-selection-menu')
		self.menu_if_inactive = Gtk.Popover.new_from_model(self.image, menu_r)
		menu_l = builder.get_object('active-selection-menu')
		self.menu_if_active = Gtk.Popover.new_from_model(self.image, menu_l)
		self.set_popovers_position(1.0, 1.0)

	def init_pixbuf(self):
		# print('⇒ init pixbuf')
		self.selection_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, \
		                                                          True, 8, 1, 1)
		self.set_coords(True, 0, 0)
		self.selection_path = None
		self.is_active = False

	def load_from_path(self, new_path):
		"""Create a selection_pixbuf from a minimal part of the main surface by
		erasing everything outside of the provided path."""
		if new_path is None:
			raise NoSelectionPathException()

		self.selection_path = new_path
		self.is_active = True
		main_pixbuf = self.image.main_pixbuf

		# Erase everything outside of the path
		surface = Gdk.cairo_surface_create_from_pixbuf(main_pixbuf, 0, None)
		surface.set_device_scale(self.image.SCALE_FACTOR, self.image.SCALE_FACTOR)
		cairo_context = cairo.Context(surface)
		cairo_context.set_operator(cairo.Operator.DEST_IN)
		cairo_context.new_path()
		cairo_context.append_path(self.selection_path)
		cairo_context.fill_preserve()
		cairo_context.set_operator(cairo.Operator.OVER)

		# Find the coords to reduce the size of what will be stored
		main_width = main_pixbuf.get_width()
		main_height = main_pixbuf.get_height()
		xmin, ymin, xmax, ymax = cairo_context.path_extents()
		xmax = min(xmax, main_width)
		ymax = min(ymax, main_height)
		xmin = int( max(xmin, 0.0) ) # If everything is right, this is selection_x
		ymin = int( max(ymin, 0.0) ) # If everything is right, this is selection_y
		if self.selection_x < 0:
			xmin = self.selection_x
		if self.selection_y < 0:
			ymin = self.selection_y

		# Actually store the pixbuf
		selection_width = int(xmax - xmin)
		selection_height = int(ymax - ymin)
		if selection_width > 0 and selection_height > 0:
			# print('⇒ load pixbuf')
			pixbuf = Gdk.pixbuf_get_from_surface(surface, int(xmin), int(ymin),\
			                                  selection_width, selection_height)
			if pixbuf is not None:
				# TODO selon un paramètre donné, remplacer un rgb par de l'alpha
				# au sein de ce pixbuf
				self.selection_pixbuf = pixbuf
			# can't use `set_pixbuf` here ^ because it would replace the free
			# path with a rectangle path
		else:
			self.reset(True)
		self.image.update_actions_state()

	def set_coords(self, temp_too, x, y):
		self.selection_x = x
		self.selection_y = y
		if temp_too:
			self.temp_x = x
			self.temp_y = y

	def set_pixbuf(self, pixbuf):
		# print('⇒ set pixbuf')
		self.selection_pixbuf = pixbuf
		self._create_path_from_pixbuf()

	def get_pixbuf(self):
		return self.selection_pixbuf

	def reset(self, update_image):
		# print('⇒ reset pixbuf')
		self.selection_pixbuf = None
		self.selection_path = None
		self.set_coords(True, 0, 0)
		self.is_active = False
		if update_image:
			self.image.update_actions_state()
			self.image.update()

	def get_path_with_scroll(self, tool_dx, tool_dy):
		# The very concept of this method sucks
		if self.selection_path is None:
			raise NoSelectionPathException()
		delta_x = tool_dx - self.image.scroll_x + self.selection_x - self.temp_x # XXX SHOULDN'T USE TEMP
		delta_y = tool_dy - self.image.scroll_y + self.selection_y - self.temp_y # XXX SHOULDN'T USE TEMP
		cairo_context = self._get_context_with_path(delta_x, delta_y)
		cairo_context.close_path()
		return cairo_context.copy_path()

	def show_selection_on_surface(self, cairo_context, with_scroll, tool_dx, tool_dy):
		if self.selection_pixbuf is None:
			raise NoSelectionPixbufException()
		if with_scroll:
			x = self.selection_x - self.image.scroll_x + tool_dx
			y = self.selection_y - self.image.scroll_y + tool_dy
		else:
			x = self.selection_x + tool_dx
			y = self.selection_y + tool_dy
		Gdk.cairo_set_source_pixbuf(cairo_context, self.selection_pixbuf, x, y)
		cairo_context.paint()

	def get_center_coords(self):
		"""Return the coords of the center of the selection."""
		w = self.selection_pixbuf.get_width()
		h = self.selection_pixbuf.get_height()
		return self.selection_x + w / 2, self.selection_y + h / 2

	############################################################################

	def _create_path_from_pixbuf(self):
		"""This method creates a rectangle selection from the currently set
		selection pixbuf.
		It can be the result of an editing operation (crop, scale, etc.), or it
		can be an imported picture (from a file or from the clipboard)."""
		if self.selection_pixbuf is None:
			raise NoSelectionPixbufException()
		self.temp_x = self.selection_x
		self.temp_y = self.selection_y
		self.is_active = True
		cairo_context = self._get_context()
		cairo_context.move_to(self.selection_x, self.selection_y)
		cairo_context.rel_line_to(self.selection_pixbuf.get_width(), 0)
		cairo_context.rel_line_to(0, self.selection_pixbuf.get_height())
		cairo_context.rel_line_to(-1 * self.selection_pixbuf.get_width(), 0)
		cairo_context.close_path()
		self.selection_path = cairo_context.copy_path()
		self.hide_popovers()
		self.image.update_actions_state()

	def point_is_in_selection(self, tested_x, tested_y):
		"""Returns a boolean if the point whose coordinates are "(tested_x,
		tested_y)" is in the path defining the selection. If such path doesn't
		exist, it returns None."""
		if not self.is_active:
			return True # shouldn't happen
		scrolled_path = self.get_path_with_scroll(self.image.scroll_x, self.image.scroll_y)
		cairo_context = self._get_context()
		cairo_context.new_path()
		cairo_context.append_path(scrolled_path)
		return cairo_context.in_fill(tested_x, tested_y)

	def _get_context(self):
		return cairo.Context(self.image.surface)

	def _get_context_with_path(self, delta_x, delta_y):
		cairo_context = self._get_context()
		for pts in self.selection_path:
			if pts[1] != ():
				x = pts[1][0] + delta_x
				y = pts[1][1] + delta_y
				cairo_context.line_to(int(x), int(y))
		return cairo_context

	############################################################################
	# Popover menus management methods #########################################

	def set_popovers_position(self, x, y):
		"""Set the coords where the popover should be opened. These coords are
		relative TO THE WIDGET, not to the pixbuf."""
		rectangle = Gdk.Rectangle()
		rectangle.x = int(x)
		rectangle.y = int(y)
		rectangle.height = 1
		rectangle.width = 1
		self.menu_if_inactive.set_pointing_to(rectangle)
		self.menu_if_active.set_pointing_to(rectangle)

	def hide_popovers(self):
		self.menu_if_active.popdown()
		self.menu_if_inactive.popdown()

	def show_popover(self):
		"""Open the adequate popover at the previously set coords."""
		if self.is_active:
			self.menu_if_active.popup()
		else:
			self.menu_if_inactive.popup()

	############################################################################
	# Future path/coords #######################################################

	def reset_future_data(self):
		self._future_x = 0
		self._future_y = 0
		self._future_path = None

	def set_future_coords(self, x, y):
		self._future_x = int(x)
		self._future_y = int(y)

	def get_future_coords(self):
		return self._future_x, self._future_y

	def set_future_path(self, path):
		self._future_path = path

	def get_future_path(self):
		return self._future_path

	def update_from_transform_tool(self, new_pixbuf, dx, dy):
		self.set_pixbuf(new_pixbuf)
		x = self.selection_x + dx
		y = self.selection_y + dy
		self.set_coords(False, x, y)
		self.set_future_coords(self._future_x + dx, self._future_y + dy)

	############################################################################
	# Debug ####################################################################

	def print_values(self, *args):
		"""Development only: is linked to the "troubleshoot selection" item in
		the short hamburger menu."""
		print("selection coords", self.selection_x, self.selection_y)
		print("temp coords", self.temp_x, self.temp_y)
		print("image.scroll coords", self.image.scroll_x, self.image.scroll_y)
		print("image.zoom_level", self.image.zoom_level)

		print("selection_path with scroll & temp deltas")
		delta_x = 0 - self.image.scroll_x + self.selection_x - self.temp_x
		delta_y = 0 - self.image.scroll_y + self.selection_y - self.temp_y
		for pts in self.selection_path:
			if pts[1] != ():
				x = pts[1][0] + delta_x
				y = pts[1][1] + delta_y
				print('\t', x, y)

		print("future path", self._future_path)
		print("future coords", self._future_x, self._future_y)
		print("---------------------------------------------------------------")

	############################################################################
################################################################################

