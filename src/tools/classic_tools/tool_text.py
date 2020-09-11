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
from gi.repository import Gtk, Gdk, Pango, PangoCairo

from .abstract_tool import AbstractAbstractTool

class ToolText(AbstractAbstractTool):
	__gtype_name__ = 'ToolText'

	def __init__(self, window, **kwargs):
		super().__init__('text', _("Text"), 'tool-text-symbolic', window)

		self.x_begin = 0.0
		self.y_begin = 0.0
		self.use_size = True
		self._should_cancel = False
		self._last_click_btn = 1

		self.font_fam_name = self.window._settings.get_string('last-font-name')
		self._bg_id = 'outline'
		self._bg_label = _("Outline")

		self.add_tool_action_simple('text-set-font', self._set_font)
		self.add_tool_action_boolean('text-bold', False)
		self.add_tool_action_boolean('text-italic', False)
		self.add_tool_action_enum('text-background', self._bg_id)

		# TODO actions sensitivity?
		self.add_tool_action_simple('text-cancel', self._on_cancel)
		self.add_tool_action_simple('text-preview', self._force_refresh)
		self.add_tool_action_simple('text-insert', self._on_insert_text)

		builder = Gtk.Builder().new_from_resource( \
		                  '/com/github/maoschanz/drawing/tools/ui/tool-text.ui')

		# Popover for text insertion
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
		dialog.set_font(self.font_fam_name) # XXX j'ai pas trop l'impression que ça marche

		# for f in PangoCairo.font_map_get_default().list_families():
		# 	print(f.get_name())
		status = dialog.run()
		if(status == Gtk.ResponseType.OK):
			self.font_fam_name = dialog.get_font_family().get_name()
			self._preview_text()
		dialog.destroy()

	def _set_font_options(self, *args):
		# XXX incomplete? OBLIQUE exists
		self._is_italic = self.get_option_value('text-italic')
		self._is_bold = self.get_option_value('text-bold')

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
		label = self.label + ' - ' + self.font_fam_name + ' - ' + self._bg_label
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
		# XXX ugly, but better in future versions
		self.main_color = self.window.color_popover_l.color_widget.get_rgba()
		self.secondary_color = self.window.color_popover_r.color_widget.get_rgba()
		self.tool_width = self.window.thickness_spinbtn.get_value_as_int()
		self.x_begin = 100
		self.y_begin = 100
		self._open_popover_at(100, 100)
		self._set_string(string)

	def _set_string(self, string):
		if string is None:
			string = ''
		self._entry.get_buffer().set_text(string, -1)

	############################################################################

	def on_press_on_area(self, event, surface, tool_width, \
	                                 left_color, right_color, event_x, event_y):
		if event.button == 1:
			self.main_color = left_color
			self.secondary_color = right_color
		else:
			self.main_color = right_color
			self.secondary_color = left_color
		self.tool_width = tool_width

	def on_release_on_area(self, event, surface, event_x, event_y):
		self._last_click_btn = event.button
		self._should_cancel = True
		self.x_begin = event_x
		self.y_begin = event_y
		self._open_popover_at(int(event.x), int(event.y))

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

	def _force_refresh(self, *args):
		if self._last_click_btn == 1:
			self.main_color = self.window.color_popover_l.color_widget.get_rgba()
			self.secondary_color = self.window.color_popover_r.color_widget.get_rgba()
		else:
			self.main_color = self.window.color_popover_r.color_widget.get_rgba()
			self.secondary_color = self.window.color_popover_l.color_widget.get_rgba()
		self.tool_width = self.window.thickness_spinbtn.get_value_as_int()
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
			'font_fam': self.font_fam_name,
			'is_italic': self._is_italic,
			'is_bold': self._is_bold,
			'font_size': self.tool_width,
			'x': self.x_begin,
			'y': self.y_begin,
			'background': self._bg_id,
			'text': self.text_string
		}
		return operation

	def do_tool_operation(self, operation):
		if operation['tool_id'] != self.id:
			return
		self.restore_pixbuf()
		cairo_context = cairo.Context(self.get_surface())

		font_fam = operation['font_fam']
		font_size = operation['font_size'] * 2
		entire_text = operation['text']
		c1 = operation['rgba1']
		c2 = operation['rgba2']
		text_x = int(operation['x'])
		text_y = int(operation['y'])

		font_description_string = font_fam
		if operation['is_italic']:
			font_description_string += " Italic"
		if operation['is_bold']:
			font_description_string += " Bold"
		font_description_string += " " + str(font_size)
		font = Pango.FontDescription(font_description_string)
		layout = PangoCairo.create_layout(cairo_context)
		layout.set_font_description(font)

		########################################################################
		# Draw background for the line #########################################

		if operation['background'] == 'rectangle':
			lines = entire_text.split('\n')
			line_y = text_y
			for line_text in lines:
				line_y = self._op_bg_rectangle(cairo_context, layout, c2, \
				                                      text_x, line_y, line_text)
		elif operation['background'] == 'shadow':
			dist = max(min(int(font_size/16), 4), 1)
			cairo_context.set_source_rgba(c2.red, c2.green, c2.blue, c2.alpha)
			self._show_text_with_options(cairo_context, layout, entire_text, \
			                                       text_x + dist, text_y + dist)
		elif operation['background'] == 'outline':
			cairo_context.set_source_rgba(c2.red, c2.green, c2.blue, c2.alpha)
			dist = max(min(int(font_size/16), 8), 1)
			for dx in range(-dist, dist):
				for dy in range(-dist, dist):
					self._show_text_with_options(cairo_context, layout, \
					                      entire_text, text_x + dx, text_y + dy)

		########################################################################
		# Draw text for the line ###############################################

		cairo_context.set_source_rgba(c1.red, c1.green, c1.blue, c1.alpha)
		self._show_text_with_options(cairo_context, layout, entire_text, \
		                                                         text_x, text_y)

		self.non_destructive_show_modif()

	def _show_text_with_options(self, cc, pl, text, text_x, text_y):
		cc.move_to(text_x, text_y)
		pl.set_text(text)
		PangoCairo.update_layout(cc, pl)
		PangoCairo.show_layout(cc, pl)

	def _op_bg_rectangle(self, context, layout, c2, text_x, line_y, line_text):
		# The text is first "displayed" in a transparent color…
		context.set_source_rgba(0.0, 0.0, 0.0, 0.50)
		self._show_text_with_options(context, layout, line_text, text_x, line_y)
		# …so we can get the size of the displayed line…
		ink_rect, logical_rect = layout.get_pixel_extents()
		delta_y = logical_rect.height
		# …and draw the background rectangle with the correct size.
		context.rel_line_to(0, delta_y)
		context.rel_line_to(logical_rect.width, 0)
		context.rel_line_to(0, -1 * delta_y)
		context.close_path()
		context.set_source_rgba(c2.red, c2.green, c2.blue, c2.alpha)
		context.fill()
		context.stroke()
		# The returned value will be used as the vertical coord of the next line
		return line_y + delta_y

	############################################################################
################################################################################

