# tool_text.py
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
from gi.repository import Gtk, Gdk
from .abstract_classic_tool import AbstractClassicTool

class ToolText(AbstractClassicTool):
	__gtype_name__ = 'ToolText'

	def __init__(self, window, **kwargs):
		super().__init__('text', _("Text"), 'tool-text-symbolic', window)

		self._should_cancel = False
		self._last_click_btn = 1

		self._font_fam = "Sans"
		self._bg_id = 'outline'
		self._bg_label = _("Outline")

		self.add_tool_action_enum('text-font', self._font_fam)
		self.add_tool_action_boolean('text-bold', False)
		self.add_tool_action_boolean('text-italic', False)
		self.add_tool_action_enum('text-background', self._bg_id)
		# TODO actions sensitivity?
		self.add_tool_action_simple('text-cancel', self._on_cancel)
		self.add_tool_action_simple('text-preview', self._force_refresh)
		self.add_tool_action_simple('text-insert', self._on_insert_text)

		builder = Gtk.Builder().new_from_resource( \
		                  '/com/github/maoschanz/drawing/tools/ui/tool_text.ui')

		# Widgets for text insertion
		self._popover = builder.get_object('insertion-popover')
		self._entry = builder.get_object('entry')
		self._entry.set_size_request(100, 50)
		self._entry.get_buffer().connect('changed', self._preview_text)
		self._hide_entry()

	############################################################################
	# Options ##################################################################

	def _set_font_options(self, *args):
		# TODO ? use the widget again, and cairo.ToyFontFace
		self._font_fam = self.get_option_value('text-font')
		if self.get_option_value('text-italic'):
			self._font_slant = cairo.FontSlant.ITALIC
		else:
			self._font_slant = cairo.FontSlant.NORMAL
		if self.get_option_value('text-bold'):
			self._font_weight = cairo.FontWeight.BOLD
		else:
			self._font_weight = cairo.FontWeight.NORMAL

	def _set_background_style(self, *args):
		state_as_string = self.get_option_value('text-background')
		self._bg_id = state_as_string
		if state_as_string == 'none':
			self._bg_label = _("No background")
		elif state_as_string == 'shadow':
			self._bg_label = _("Shadow")
		elif state_as_string == 'outline':
			self._bg_label = _("Outline")
		else:
			self._bg_label = _("Rectangle background")

	def get_options_label(self):
		return _("Font options")

	def get_edition_status(self):
		self._set_background_style()
		self._set_font_options()
		label = self.label + ' - ' + self._font_fam + ' - ' + self._bg_label
		return label

	############################################################################

	def on_tool_selected(self):
		super().on_tool_selected()
		self._last_click_btn = 1

	def on_tool_unselected(self):
		self.set_action_sensitivity('paste', True)
		self.set_action_sensitivity('select_all', True)
		self.set_action_sensitivity('selection_cut', True)
		self.set_action_sensitivity('selection_copy', True)

	def give_back_control(self, preserve_selection):
		if self._should_cancel:
			self._on_cancel()

	def force_text_tool(self, string):
		self.row.set_active(True)
		self.set_common_values(self._last_click_btn)
		self.on_release_on_area(None, None, 100, 100)
		self._set_string(string)

	def _set_string(self, string):
		self._entry.get_buffer().set_text(string, -1)

	############################################################################

	# XXX better way to move the text ?

	def on_release_on_area(self, event, surface, event_x, event_y):
		self._last_click_btn = event.button
		self._should_cancel = True
		self.set_common_values(self._last_click_btn)
		self.x_press = event_x
		self.y_press = event_y
		# self._set_font_options()

		self._open_popover_at(int(event.x), int(event.y))

		# Usual text entry shortcuts don't work otherwise
		self.set_action_sensitivity('paste', False)
		self.set_action_sensitivity('select_all', False)
		self.set_action_sensitivity('selection_cut', False)
		self.set_action_sensitivity('selection_copy', False)

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

	def _hide_entry(self):
		self._popover.popdown()

	def _force_refresh(self, *args):
		self.set_common_values(self._last_click_btn)
		# self._set_font_options()
		self._preview_text()

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

	def _on_cancel(self, *args):
		self._hide_entry()
		self._set_string('')
		self._should_cancel = False

	############################################################################

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'rgba1': self.main_color,
			'rgba2': self.secondary_color,
			'_font_fam': self._font_fam,
			'_font_slant': self._font_slant,
			'_font_weight': self._font_weight,
			'font_size': self.tool_width,
			'x': self.x_press,
			'y': self.y_press,
			'background': self._bg_id,
			'text': self.text_string
		}
		return operation

	def do_tool_operation(self, operation):
		self.start_tool_operation(operation)
		cairo_context = self.get_context()

		_font_fam = operation['_font_fam']
		_font_slant = operation['_font_slant']
		_font_weight = operation['_font_weight']
		font_size = operation['font_size'] * 3 # XXX totalement arbitraire
		cairo_context.select_font_face(_font_fam, _font_slant, _font_weight)
		cairo_context.set_font_size(font_size)

		lines = operation['text'].split('\n')
		i = 0
		c1 = operation['rgba1']
		c2 = operation['rgba2']
		text_x = int(operation['x'])
		text_y = int(operation['y'])

		for line_text in lines:
			####################################################################
			# Draw background for the line #####################################
			line_y = text_y + i * font_size
			if operation['background'] == 'rectangle':
				self._op_bg_rectangle(cairo_context, c2, font_size, i, text_x, \
				                                              text_y, line_text)
			elif operation['background'] == 'shadow':
				self._op_bg_shadow(cairo_context, c2, font_size, text_x, \
				                                              line_y, line_text)
			elif operation['background'] == 'outline':
				self._op_bg_outline(cairo_context, c2, font_size, text_x, \
				                                              line_y, line_text)
			####################################################################
			# Draw text for the line ###########################################
			cairo_context.set_source_rgba(c1.red, c1.green, c1.blue, c1.alpha)
			cairo_context.move_to(text_x, line_y)
			cairo_context.show_text( line_text )
			i = i + 1
		self.non_destructive_show_modif()

	def _op_bg_shadow(self, context, color, font_size, text_x, text_y, line):
		context.set_source_rgba(color.red, color.green, color.blue, color.alpha)
		dist = max(min(int(font_size/18), 4), 1)
		context.move_to(text_x + dist, text_y + dist)
		context.show_text(line)

	def _op_bg_outline(self, context, color, font_size, text_x, text_y, line):
		context.set_source_rgba(color.red, color.green, color.blue, color.alpha)
		dist = max(min(int(font_size/18), 8), 1)
		for dx in range(-dist, dist):
			for dy in range(-dist, dist):
				context.move_to(text_x + dx, text_y + dy)
				context.show_text(line)

	def _op_bg_rectangle(self, context, color, font_size, i, text_x, text_y, line):
		# XXX i think cairo.Context.font_extents is supposed to help me
		context.set_source_rgba(0.0, 0.0, 0.0, 0.0)
		first_y = int(text_y + (i + 0.2) * font_size)
		context.move_to(text_x, first_y)
		context.show_text(line)
		context.rel_line_to(0, (-1) * font_size)
		context.line_to(text_x, int(text_y + (i - 0.8) * font_size))
		context.line_to(text_x, first_y)
		context.set_source_rgba(color.red, color.green, color.blue, color.alpha)
		context.fill()
		context.stroke()

	############################################################################
################################################################################

