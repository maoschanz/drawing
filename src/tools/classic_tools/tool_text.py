# tool_text.py
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

import cairo
from gi.repository import Gtk, Gdk, GLib, Pango, PangoCairo
from .abstract_classic_tool import AbstractClassicTool
from .utilities_overlay import utilities_show_composite_overlay

class ToolText(AbstractClassicTool):
	__gtype_name__ = 'ToolText'

	def __init__(self, window, **kwargs):
		super().__init__('text', _("Text"), 'tool-text-symbolic', window)

		# There are several types of possible interactions with the canvas,
		# depending on where the pointer is during the press event.
		self._pointer_target = 'input' # input, resize, move, apply

		# Weird ass caching (`_text_x0` and `_text_y0` are only updated when
		# releasing a 'move' interaction) to avoid erratic motion of the preview
		self._text_x = self._text_x0 = 0
		self._text_y = self._text_y0 = 0

		# These values are found during the operation computation, and are
		# re-used when rendering the previewed overlay
		self._preview_width = 0
		self._preview_height = 0

		self.add_tool_action_simple('text-set-font', self._set_font)
		self.add_tool_action_boolean('text-bold', False)
		self.add_tool_action_boolean('text-italic', False)

		self._background_id = self.load_tool_action_enum('text-background', \
		                                                 'last-text-background')
		self._font_fam_name = self.load_tool_action_enum('text-active-family', \
		                                                 'last-font-name')

		# XXX actions sensitivity?
		self.add_tool_action_simple('text-cancel', self._on_cancel)
		self.add_tool_action_simple('text-insert', self._on_insert_text)

		builder = Gtk.Builder().new_from_resource(self.UI_PATH + 'tool-text.ui')
		# Widgets for text insertion
		self._popover = builder.get_object('insertion-popover')
		self._entry = builder.get_object('entry')
		self._entry.set_size_request(100, 50)
		self._entry.get_buffer().connect('changed', self._preview_text)
		self._hide_entry()

	############################################################################
	# Options ##################################################################

	def _set_font(self, *args):
		dialog = Gtk.FontChooserDialog(show_preview_entry=False)
		dialog.set_level(Gtk.FontChooserLevel.FAMILY)
		dialog.set_font(self._font_fam_name)

		# for f in PangoCairo.font_map_get_default().list_families():
		# 	print(f.get_name())

		try:
			status = dialog.run()
			# ^ FIXME #479
		except Exception as ex:
			# probablement qu'on ne catchera rien
			pass
		if(status == Gtk.ResponseType.OK):
			self._font_fam_name = dialog.get_font_family().get_name()
			# print(dialog.get_font())
			font_gvar = GLib.Variant.new_string(self._font_fam_name)
			self.window.lookup_action('text-active-family').set_state(font_gvar)
			self._preview_text()
		dialog.destroy()
		self.window.on_tool_options_changed()

	def _set_font_options(self, *args):
		# XXX incomplete? OBLIQUE exists
		self._is_italic = self.get_option_value('text-italic')
		self._is_bold = self.get_option_value('text-bold')

	def _set_background_style(self, *args):
		self._background_id = self.get_option_value('text-background')

	def get_options_label(self):
		return _("Text options")

	def get_editing_tips(self):
		if self._has_current_text():
			label_move = self.label + " - " + _("Grab the rectangle to adjust the text position")
			label_apply = self.label + " - " + _("Click outside the rectangle to apply")
		else:
			label_move = None
			label_apply = None

		label_options = self.label + " - " + self._font_fam_name
		if self._background_id != 'none':
			bg_label = {
				'none': _("No background"),
				'shadow': _("Shadow"),
				'thin-outline': _("Thin outline"),
				'thick-outline': _("Thick outline"),
				'rectangle': _("Rectangle background"),
			}[self._background_id]
			label_options += " - " + bg_label

		full_list = [label_options, label_move, label_apply]
		return list(filter(None, full_list))

	def on_options_changed(self):
		super().on_options_changed()
		self._set_font_options()
		self._set_background_style()
		self._preview_text()

	############################################################################

	def on_tool_unselected(self):
		self.set_action_sensitivity('paste', True)
		self.set_action_sensitivity('select_all', True)
		self.set_action_sensitivity('selection_cut', True)
		self.set_action_sensitivity('selection_copy', True)

	def give_back_control(self, preserve_selection, next_tool=None):
		if self._has_current_text():
			operation = self.build_operation()
			self.apply_operation(operation)
			self._set_string('')
		else:
			self._on_cancel()
		return next_tool

	def force_text_tool(self, string):
		self.select_flowbox_child()
		# XXX déterminer des coordonnées qui fassent sens quel que soit l'état
		# du scrolling et du zoom
		self.set_common_values(self._last_btn, 100, 100)
		self._open_popover_at(100, 100)
		self._set_string(string)

	def _set_string(self, string):
		if string is None:
			string = ''
		self._entry.get_buffer().set_text(string, -1)

	############################################################################

	def on_press_on_area(self, event, surface, event_x, event_y):
		self.set_common_values(event.button, event_x, event_y)
		self._pointer_target = 'input'
		if not self._has_current_text():
			return

		should_input, should_move = self.on_draw_above(None, self.get_context())
		if should_input:
			return
		elif not should_move:
			self._pointer_target = 'apply'
			# FIXME avoir appelé set_common_values alors qu'on va juste apply me
			# semble être une grosse erreur d'UX
			return

		self._pointer_target = 'move'

	def on_motion_on_area(self, event, surface, event_x, event_y, render=True):
		if 'move' == self._pointer_target:
			self._text_x = self._text_x0 + (event_x - self.x_press)
			self._text_y = self._text_y0 + (event_y - self.y_press)
		if not render:
			return
		self._preview_text()

	def on_release_on_area(self, event, surface, event_x, event_y):
		if 'input' == self._pointer_target:
			if not self._has_current_text():
				self.set_common_values(event.button, event_x, event_y)
				self._text_x = self._text_x0 = event_x
				self._text_y = self._text_y0 = event_y
			self._open_popover_at(event.x, event.y)
		elif 'apply' == self._pointer_target:
			self._on_insert_text()
		elif 'move' == self._pointer_target:
			self.on_motion_on_area(event, surface, event_x, event_y)
			self._text_x0 = self._text_x
			self._text_y0 = self._text_y

	# XXX could there be a better way to input the text ?
	def _open_popover_at(self, x, y):
		rectangle = Gdk.Rectangle()
		rectangle.x = x
		rectangle.y = y
		rectangle.height = 1
		rectangle.width = 1
		self._popover.set_pointing_to(rectangle)
		self._popover.set_relative_to(self.get_image())
		self._popover.popup()
		self._entry.grab_focus()
		self._preview_text()

		# Usual text entry shortcuts don't work otherwise
		self.set_action_sensitivity('paste', False)
		self.set_action_sensitivity('select_all', False)
		self.set_action_sensitivity('selection_cut', False)
		self.set_action_sensitivity('selection_copy', False)

	def _hide_entry(self):
		self._popover.popdown()

	def _on_insert_text(self, *args):
		self._hide_entry()
		if self._has_current_text():
			operation = self.build_operation()
			self.apply_operation(operation)
			self._set_string('')
		self.set_action_sensitivity('paste', True)
		self.set_action_sensitivity('select_all', True)
		self.set_action_sensitivity('selection_cut', True)
		self.set_action_sensitivity('selection_copy', True)

	def _has_current_text(self):
		b = self._entry.get_buffer()
		self.text_string = b.get_text(b.get_start_iter(), b.get_end_iter(), False)
		if self.text_string == '':
			self.restore_pixbuf()
			self.non_destructive_show_modif()
			return False
		else:
			return True

	def _preview_text(self, *args):
		if self._has_current_text():
			operation = self.build_operation()
			self.do_tool_operation(operation)

	def on_draw_above(self, area, ccontext):
		if not self._has_current_text():
			return

		sorigin_x = -1 * self.get_image().scroll_x
		sorigin_y = -1 * self.get_image().scroll_y
		if area is None:
			sorigin_x = 0
			sorigin_y = 0

		actual_width = self._preview_width
		actual_height = self._preview_height

		ccontext.new_path()
		ccontext.move_to(sorigin_x, sorigin_y)
		ccontext.rel_move_to(self._text_x, self._text_y)
		ccontext.rel_line_to(actual_width, 0)
		ccontext.rel_line_to(0, actual_height)
		ccontext.rel_line_to(-1 * actual_width, 0)
		ccontext.rel_line_to(0, -1 * actual_height)

		should_input = ccontext.in_fill(self.x_press, self.y_press)

		thickness = self.get_overlay_thickness()
		should_move = utilities_show_composite_overlay(ccontext, thickness, \
		                     sorigin_x + self.x_press, sorigin_y + self.y_press)

		return should_input, should_move

	def _on_cancel(self, *args):
		self._hide_entry()
		self._set_string('')

	def on_unclicked_motion_on_area(self, event, surface):
		if not self._has_current_text():
			self.cursor_name = 'text'
		else:
			self.cursor_name = 'pointer'
		self.window.set_cursor(True)

	############################################################################

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'rgba1': self.main_color,
			'rgba2': self.secondary_color,
			'font_fam': self._font_fam_name,
			'is_italic': self._is_italic,
			'is_bold': self._is_bold,
			'font_size': self.tool_width,
			'antialias': self._use_antialias,
			'x': self._text_x,
			'y': self._text_y,
			'background': self._background_id,
			'text': self.text_string
		}
		return operation

	def do_tool_operation(self, operation):
		cairo_context = self.start_tool_operation(operation)

		font_fam = operation['font_fam']
		font_size = operation['font_size'] * 2
		entire_text = operation['text']
		background_color = operation['rgba2']
		text_x = operation['x']
		text_y = operation['y']

		font_description_string = font_fam
		if operation['is_italic']:
			font_description_string += " Italic"
		if operation['is_bold']:
			font_description_string += " Bold"
		font_description_string += " " + str(font_size)
		font = Pango.FontDescription(font_description_string)

		p_context = PangoCairo.create_context(cairo_context)
		layout = Pango.Layout(p_context)
		layout.set_font_description(font)

		if not operation['antialias']:
			font_options = cairo.FontOptions()
			font_options.set_antialias(cairo.Antialias.NONE)
			font_options.set_hint_metrics(cairo.HintMetrics.OFF)
			font_options.set_hint_style(cairo.HintStyle.FULL)
			PangoCairo.context_set_font_options(p_context, font_options)

		########################################################################
		# Draw background ######################################################

		if operation['background'] == 'rectangle':
			lines = entire_text.split('\n')
			line_y = text_y
			for line_text in lines:
				line_y = self._op_bg_rectangle(cairo_context, layout, \
				                    background_color, text_x, line_y, line_text)
		elif operation['background'] == 'shadow':
			dist = max(min(int(font_size/16), 4), 1)
			cairo_context.set_source_rgba(*background_color)
			self._show_text_at_coords(cairo_context, layout, entire_text, \
			                                       text_x + dist, text_y + dist)
		elif operation['background'] == 'thin-outline':
			cairo_context.set_source_rgba(*background_color)
			dist = min(int(font_size/16), 10)
			dist = max(dist, 2)
			for dx in range(-dist, dist):
				for dy in range(-dist, dist):
					if abs(dx) + abs(dy) <= dist * 1.5:
						self._show_text_at_coords(cairo_context, layout, \
						                  entire_text, text_x + dx, text_y + dy)
			# these `for`s and this `if` should outline with an octogonal shape,
			# which is close enough to a smooth round outline imho.
		elif operation['background'] == 'thick-outline':
			cairo_context.set_source_rgba(*background_color)
			dist = int(font_size/10)
			dist = max(dist, 2)
			for dx in range(-dist, dist):
				for dy in range(-dist, dist):
					if abs(dx) + abs(dy) <= dist * 1.5:
						self._show_text_at_coords(cairo_context, layout, \
						                  entire_text, text_x + dx, text_y + dy)
			# looks better, but so much computation for bullshit...

		########################################################################
		# Draw text ############################################################

		cairo_context.set_source_rgba(*operation['rgba1'])
		self._show_text_at_coords(cairo_context, layout, entire_text, \
		                                                         text_x, text_y)

		ink_rect, logical_rect = layout.get_pixel_extents()
		self._preview_width = logical_rect.width
		self._preview_height = logical_rect.height

		self.non_destructive_show_modif()

	def _show_text_at_coords(self, cairo_c, pango_l, text, text_x, text_y):
		"""Use a pango layout (pango_l) to show a line of text (text) on a cairo
		context (cairo_c) at given coordinates (text_x, text_y)."""
		cairo_c.move_to(text_x, text_y)
		pango_l.set_text(text, -1)
		PangoCairo.update_layout(cairo_c, pango_l)
		PangoCairo.show_layout(cairo_c, pango_l)

	def _op_bg_rectangle(self, context, layout, c2, text_x, line_y, line_text):
		# The text is first "displayed" in a transparent color…
		context.set_source_rgba(0.0, 0.0, 0.0, 0.0)
		self._show_text_at_coords(context, layout, line_text, text_x, line_y)
		# …so we can get the size of the displayed line…
		ink_rect, logical_rect = layout.get_pixel_extents()
		delta_y = logical_rect.height
		# …and draw the background rectangle with the correct size.
		context.rel_line_to(0, delta_y)
		context.rel_line_to(logical_rect.width, 0)
		context.rel_line_to(0, -1 * delta_y)
		context.close_path()
		context.set_source_rgba(*c2)
		context.fill()
		context.stroke()
		# The returned value will be used as the vertical coord of the next line
		return line_y + delta_y

	############################################################################
################################################################################

