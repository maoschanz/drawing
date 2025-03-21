# tool_scale.py
#
# Copyright 2018-2023 Romain F. T.
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
from .abstract_transform_tool import AbstractCanvasTool
from .optionsbar_scale import OptionsBarScale
from .utilities_overlay import utilities_show_handles_on_context

class ToolScale(AbstractCanvasTool):
	__gtype_name__ = 'ToolScale'

	def __init__(self, window):
		super().__init__('scale', _("Scale"), 'tool-scale-symbolic', window)
		self.cursor_name = 'not-allowed'

		# depends on both the option AND the click coordinates
		self._preserve_ratio = True

		# the user inverted the ratio preservation behavior with a modifier key
		self._ratio_is_inverted = False

		# safety lock to reload asynchronously
		self._reload_is_locked = False

		# safety lock to set values in the spinbuttons
		self._spinbtns_disabled = True

		self._x = 0
		self._y = 0
		self._x2 = 0
		self._y2 = 0
		self.x_press = self.x_motion = None
		self.y_press = self.y_motion = None
		self.add_tool_action_enum('scale-proportions', 'corners')
		self.add_tool_action_boolean('scale-ratio-spinbtns', False)
		self.add_tool_action_enum('scale-unit', 'pixels')

	def try_build_pane(self):
		self.pane_id = 'scale'
		self.window.options_manager.try_add_bottom_pane(self.pane_id, self)

	def build_bottom_pane(self):
		bar = OptionsBarScale(self)

		self._width_btn = bar.width_btn
		self._height_btn = bar.height_btn
		self._width_btn.connect('value-changed', self.on_spinbtn_changed)
		self._height_btn.connect('value-changed', self.on_spinbtn_changed)

		self._w100_btn = bar.width_100_btn
		self._h100_btn = bar.height_100_btn
		self._w100_btn.connect('value-changed', self.on_spinbtn100_changed)
		self._h100_btn.connect('value-changed', self.on_spinbtn100_changed)

		return bar

	############################################################################

	def get_options_label(self):
		return _("Scaling options")

	def get_editing_tips(self):
		if self.apply_to_selection:
			label_action = _("Scaling the selection")
			label_confirm = None
		else:
			label_action = _("Scaling the canvas")
			label_confirm = self.label + " - " + \
			                         _("Don't forget to confirm the operation!")

		if self.get_image().get_mouse_is_pressed():
			label_modifier_shift = None
		else:
			label_modifier_shift = _("Press <Shift> to quickly toggle the " + \
			                                        "'lock proportions' option")

		# there is intentionally no `label_direction` because i expect the users
		# to understand by themselves how it works.

		full_list = [label_action, label_confirm, label_modifier_shift]
		return list(filter(None, full_list))

	def on_options_changed(self):
		# 1) update the visibility of the spinbuttons depending on which ones
		# the user wants to use.
		want_pixels = self.get_option_value('scale-unit') == 'pixels'
		if want_pixels:
			self._width_btn.set_visible(True)
			self._height_btn.set_visible(True)
			self._w100_btn.set_visible(False)
			self._h100_btn.set_visible(False)
		else:
			self._width_btn.set_visible(False)
			self._height_btn.set_visible(False)
			self._w100_btn.set_visible(True)
			self._h100_btn.set_visible(True)

		# 2) update the bullshit around ratio preservation actions
		ratio_option = self.get_option_value('scale-proportions')
		if not ratio_option == 'corners':
			action = self.window.lookup_action('scale-ratio-spinbtns')
			action.set_state(GLib.Variant.new_boolean(ratio_option == 'always'))
		self.set_action_sensitivity('scale-ratio-spinbtns', ratio_option == 'corners')

	def on_tool_selected(self, *args):
		super().on_tool_selected()
		self._x = 0
		self._y = 0
		self.x_press = self.x_motion = None
		self.y_press = self.y_motion = None
		self._w100_btn.set_value(100)
		self._h100_btn.set_value(100)

		width, height = self._get_original_size()
		self.set_preserve_ratio()
		self._ratio = width / height
		self._spinbtns_disabled = False
		self._width_btn.set_value(width)
		self._height_btn.set_value(height)
		self._previous_width = width
		self._previous_height = height
		self.build_and_do_op() # Ensure a correct preview

	def _get_original_size(self):
		if self.apply_to_selection:
			original_pixbuf = self.get_selection_pixbuf()
		else:
			original_pixbuf = self.get_main_pixbuf()
		return original_pixbuf.get_width(), original_pixbuf.get_height()

	############################################################################

	def set_preserve_ratio(self, for_spinbtns=False):
		"""Set whether or not `self._preserve_ratio` should be true. If it is,
		AND that wasn't already the case before, this method sets the value of
		`self._ratio` too.
		The parameter is `True` if the request to set the ratio is triggered by
		a direct interaction with a spinbutton: the method will not look at the
		same options to decide what to do."""
		former_setting = self._preserve_ratio

		if for_spinbtns:
			self._preserve_ratio = self.get_option_value('scale-ratio-spinbtns')
		else:
			setting = self.get_option_value('scale-proportions')
			if setting == 'corners':
				self._preserve_ratio = len(self._directions) != 1
			else:
				self._preserve_ratio = setting == 'always'

		if self._ratio_is_inverted:
			self._preserve_ratio = not self._preserve_ratio

		if self._preserve_ratio == former_setting:
			return
		if self._preserve_ratio:
			if for_spinbtns:
			    self._ratio = self._get_previous_width() / self._get_previous_height()
			else:
			    self._ratio = self._get_width() / self._get_height()

	def _try_scale_dimensions(self):
		if self._reload_is_locked:
			return
		self._reload_is_locked = True
		GLib.timeout_add(100, self._unlock_reload, {})
		self._async_try_scale_dimensions()

	def _unlock_reload(self, content_params):
		self._reload_is_locked = False
		self._async_try_scale_dimensions()

	def _async_try_scale_dimensions(self, data_dict={}):
		"""When the value in a spinbutton changes, adjust the values in the
		spinbuttons if necessary, and build-and-do the corresponding tool
		operation."""
		self._spinbtns_disabled = True

		if self._preserve_ratio:
			temp_pixbuf = self.get_image().temp_pixbuf
			existing_width = temp_pixbuf.get_width()
			existing_height = temp_pixbuf.get_height()

			new_width = self._get_width()
			new_height = self._get_height()

			if existing_width != new_width:
				new_height = new_width / self._ratio
				self._height_btn.set_value(new_height)
			if existing_height != new_height:
				new_width = new_height * self._ratio
				self._width_btn.set_value(new_width)
		# else:
			# If the ratio isn't locked, the dimension should be applied without
			# any change. Calculations to adjust the size are only useful when
			# trying to preserve the image proportions.

		# Update the "percentage" spinbuttons
		original_width , original_height = self._get_original_size()
		new_w100 = 100 * (self._get_width() / original_width)
		new_h100 = 100 * (self._get_height() / original_height)
		self._w100_btn.set_value(new_w100)
		self._h100_btn.set_value(new_h100)

		self._spinbtns_disabled = False
		self.build_and_do_op()

	############################################################################
	# Spinbuttons management ###################################################

	def on_spinbtn_changed(self, *args):
		if self._spinbtns_disabled:
			return
		if self.x_press is None:
			# This means the user interacts with the spinbtn directly, instead
			# of the surface.
			self.set_preserve_ratio(True)
		self._try_scale_dimensions()

		if not self._preserve_ratio:
		    self._previous_width = self._get_width()
		    self._pervious_height = self._get_height()

	def on_spinbtn100_changed(self, *args):
		if self._spinbtns_disabled:
			return
		# This callback can only pass its guard clause when triggered from the
		# spinbutton directly: i don't have to check the value of self.x_press
		self.set_preserve_ratio(True)

		original_width, original_height = self._get_original_size()
		new_width = original_width * (self._w100_btn.get_value() / 100)
		new_height = original_height * (self._h100_btn.get_value() / 100)
		delta_x = self._get_width() - new_width
		delta_y = self._get_height() - new_height
		self._apply_deltas_to_spinbtns(new_width, new_height, delta_x, delta_y)

	def _apply_deltas_to_spinbtns(self, new_width, new_height, dx=0, dy=0):
		if self._preserve_ratio:
			if abs(dy) > abs(dx):
				self._height_btn.set_value(new_height)
			else:
				self._width_btn.set_value(new_width)
		else:
			self._height_btn.set_value(new_height)
			self._width_btn.set_value(new_width)
		self._previous_height = new_height
		self._previous_width = new_width

	def _get_width(self):
		return self._width_btn.get_value_as_int()

	def _get_height(self):
		return self._height_btn.get_value_as_int()

	def _get_previous_width(self):
	    try:
	        return self._previous_width
	    finally:
	        self._previous_width = self._get_width()

	def _get_previous_height(self):
	    try:
	        return self._previous_height
	    finally:
	        self._previous_height = self._get_height()

	############################################################################

	def on_unclicked_motion_on_area(self, event, surface):
		self.set_directional_cursor(event.x, event.y)

	def on_press_on_area(self, event, surface, event_x, event_y):
		self.update_modifier_state(event.state)
		if 'SHIFT' in self._modifier_keys:
			# The value will be restored later in `on_release_on_area`
			self._ratio_is_inverted = True

		self.x_press = self.x_motion = event_x
		self.y_press = self.y_motion = event_y
		self._x2 = self._x + self._get_width()
		self._y2 = self._y + self._get_height()
		self.set_preserve_ratio()

	def on_motion_on_area(self, event, surface, event_x, event_y, render=True):
		if self._directions == '':
			return
		delta_x = event_x - self.x_motion
		delta_y = event_y - self.y_motion
		self.x_motion = event_x
		self.y_motion = event_y

		height = self._get_height()
		width = self._get_width()
		if 'n' in self._directions:
			height -= delta_y
			self._y = self._y + delta_y
		if 's' in self._directions:
			height += delta_y
		if 'w' in self._directions:
			width -= delta_x
			self._x = self._x + delta_x
		if 'e' in self._directions:
			width += delta_x

		if self.apply_to_selection and self._preserve_ratio:
			if 'w' in self._directions:
				self._x = self._x2 - width
			if 'n' in self._directions:
				self._y = self._y2 - height

		self._apply_deltas_to_spinbtns(width, height, delta_x, delta_y)

	def on_release_on_area(self, event, surface, event_x, event_y):
		self.on_motion_on_area(event, surface, event_x, event_y)
		self._ratio_is_inverted = False
		self.build_and_do_op() # technically already done
		self._scroll_to_end(event_x - self.x_press, event_y - self.y_press)

		# Reset those to tell apart a spinbtn signals' possible origins
		self.x_press = self.x_motion = None
		self.y_press = self.y_motion = None

	############################################################################

	def on_draw_above(self, area, cairo_context):
		if self.apply_to_selection:
			x1 = int(self._x)
			y1 = int(self._y)
		else:
			x1 = 0
			y1 = 0
		x2 = x1 + self._get_width()
		y2 = y1 + self._get_height()
		x1, x2, y1, y2 = self.get_image().get_corrected_coords(x1, x2, y1, y2, \
		                                         self.apply_to_selection, False)
		self._draw_temp_pixbuf(cairo_context, x1, y1)
		thickness = self.get_overlay_thickness()
		utilities_show_handles_on_context(cairo_context, x1, x2, y1, y2, thickness)

	############################################################################

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'is_selection': self.apply_to_selection,
			'is_preview': True,
			'local_dx': int(self._x),
			'local_dy': int(self._y),
			'width': self._get_width(),
			'height': self._get_height()
		}
		return operation

	def do_tool_operation(self, operation):
		self.start_tool_operation(operation)
		if operation['is_selection']:
			source_pixbuf = self.get_selection_pixbuf()
		else:
			source_pixbuf = self.get_main_pixbuf()
		self.get_image().set_temp_pixbuf(source_pixbuf.scale_simple( \
		                                 operation['width'], \
		                                 operation['height'], \
		                                 GdkPixbuf.InterpType.TILES))
		self.common_end_operation(operation)

	############################################################################
################################################################################

