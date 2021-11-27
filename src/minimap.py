# Licensed under GPL3 https://github.com/maoschanz/drawing/blob/master/LICENSE

import cairo
from gi.repository import Gtk, Gdk, GdkPixbuf
from .utilities_overlay import utilities_show_overlay_on_context

class DrMinimap(Gtk.Popover):
	__gtype_name__ = 'DrMinimap'
	# TODO custom "move" cursor and "on_motion" method?

	def __init__(self, window, minimap_btn, **kwargs):
		super().__init__(**kwargs)
		self._window = window
		self._preview_size = self._window.gsettings.get_int('preview-size')
		self.mini_pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 300, 300)
		self._mini_surface = cairo.ImageSurface(cairo.Format.ARGB32, 5, 5)

		builder = Gtk.Builder.new_from_resource( \
		                          '/com/github/maoschanz/drawing/ui/minimap.ui')
		box = builder.get_object('minimap_box')

		self._zoom_scale = builder.get_object('_zoom_scale')
		self._zoom_scale.add_mark(100.0, Gtk.PositionType.TOP, None)
		self._zoom_scale.connect('value-changed', self._update_zoom_level)

		self._minimap_area = builder.get_object('_minimap_area')
		self._minimap_area.set_size(200, 200)
		self._minimap_area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | \
		                                      Gdk.EventMask.BUTTON_RELEASE_MASK)
		self._minimap_area.connect('draw', self._on_mm_draw)
		self._minimap_area.connect('button-press-event', self._on_mm_press)
		self._minimap_area.connect('button-release-event', self._on_mm_release)

		self.add(box)
		self.connect('closed', self._on_popover_dismissed)
		self.set_relative_to(minimap_btn)

	def set_zoom_label(self, int_value):
		# This string displays the zoom level: %s will be replaced with a
		# number, while %% will be rendered as the symbol '%'
		zoom_label = _("%s%%") % str(int(int_value))
		self._window.options_manager.set_minimap_label(zoom_label)
		self.update_minimap()

	def update_zoom_scale(self, value):
		self._zoom_scale.set_value(value * 100)


	def update_minimap(self, force_update=False):
		"""Update the overlay on the minimap, based on the scroll coordinates."""
		if not self.get_visible() and not force_update:
			return
		image = self._window.get_active_image()
		self.mini_pixbuf = image.generate_mini_pixbuf(self._preview_size)
		self._mini_surface = Gdk.cairo_surface_create_from_pixbuf( \
		                                              self.mini_pixbuf, 0, None)
		pix_width = self.mini_pixbuf.get_width()
		pix_height = self.mini_pixbuf.get_height()
		self._minimap_area.set_size_request(pix_width, pix_height)

		# TODO if possible, updating the overlay should be doable without first
		# rebuilding the pixbuf and the surface. It's not very useful however
		# since the guard clause prevent the update in most cases anyway.
		if image.get_need_minimap_overlay():
			size_ratio = image.get_minimap_ratio(pix_width)
			mini_x = int(image.scroll_x * size_ratio)
			mini_y = int(image.scroll_y * size_ratio)
			visible_width, visible_height = image.get_visible_size()
			mini_width = int(visible_width * size_ratio)
			mini_height = int(visible_height * size_ratio)
			mini_context = cairo.Context(self._mini_surface)
			mini_context.move_to(mini_x, mini_y)
			mini_context.line_to(mini_x, mini_height + mini_y)
			mini_context.line_to(mini_width + mini_x, mini_height + mini_y)
			mini_context.line_to(mini_width + mini_x, mini_y)
			mini_context.close_path()
			mini_path = mini_context.copy_path()
			utilities_show_overlay_on_context(mini_context, mini_path, False)
		# else:
		# 	???
		self._minimap_area.queue_draw()
		image.update()

	############################################################################

	def _update_zoom_level(self, *args):
		zoom_value = self._zoom_scale.get_value()
		if self._window.get_active_image().zoom_level != zoom_value/100:
			self._window.get_active_image().zoom_level = zoom_value/100
			self._window.get_active_image().update()
		self.set_zoom_label(zoom_value)

	def _on_popover_dismissed(self, *args):
		"""Callback of the 'closed' signal, updating the state of the action."""
		try:
			self.get_relative_to().set_active(False)
		except:
			pass

	def _on_mm_draw(self, area, cairo_context):
		"""Callback of the 'draw' signal, painting the area with the surface."""
		cairo_context.set_source_surface(self._mini_surface, 0, 0)
		cairo_context.paint()

	def _on_mm_press(self, area, event):
		"""Callback of the 'button-press-event' signal."""
		self._old_x = event.x
		self._old_y = event.y

	def _on_mm_release(self, area, event):
		"""Callback of the 'button-release-event' signal."""
		image = self._window.get_active_image()
		size_ratio = image.get_minimap_ratio(self.mini_pixbuf.get_width())
		delta_x = int((event.x - self._old_x) / size_ratio)
		delta_y = int((event.y - self._old_y) / size_ratio)
		image.add_deltas(delta_x, delta_y, 1)

	############################################################################
################################################################################

