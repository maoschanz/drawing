# tool_text.py

import cairo
from gi.repository import Gtk, Gdk

from .abstract_classic_tool import AbstractClassicTool

class ToolText(AbstractClassicTool):
	__gtype_name__ = 'ToolText'

	def __init__(self, window, **kwargs):
		super().__init__('text', _("Text"), 'tool-text-symbolic', window)

		self.x_begin = 0.0
		self.y_begin = 0.0
		self.should_cancel = False
		self.use_size = True

		self.font_fam = "Sans"
		self.background_id = 'outline'
		self.background_label = _("Outline")

		self.add_tool_action_enum('text_font', self.font_fam)
		self.add_tool_action_boolean('text_bold', False)
		self.add_tool_action_boolean('text_italic', False)
		self.add_tool_action_enum('text_background', self.background_id)

		builder = Gtk.Builder().new_from_resource( \
		                  '/com/github/maoschanz/drawing/tools/ui/tool_text.ui')

		# Popover for text insertion TODO widgets on the GtkLayout ?
		self.popover = builder.get_object('insertion-popover')
		self.entry = builder.get_object('entry')
		self.entry.set_size_request(100, 50)
		insert_btn = builder.get_object('insert_btn')
		insert_btn.connect('clicked', self.on_insert_text)
		cancel_btn = builder.get_object('cancel_btn')
		cancel_btn.connect('clicked', self.on_cancel)
		self.entry.get_buffer().connect('changed', self.preview_text)

	############################################################################
	# Options ##################################################################

	def set_font(self, *args):
		self.font_fam = self.get_option_value('text_font')

	def set_background_style(self, *args):
		state_as_string = self.get_option_value('text_background')
		self.background_id = state_as_string
		if state_as_string == 'none':
			self.background_label = _("No background")
		elif state_as_string == 'shadow':
			self.background_label = _("Shadow")
		elif state_as_string == 'outline':
			self.background_label = _("Outline")
		else:
			self.background_label = _("Rectangle background")

	def get_options_label(self):
		return _("Font options")

	def get_edition_status(self):
		self.set_background_style()
		# TODO + font ?
		label = self.label + ' - ' + self.font_fam + ' - ' + self.background_label
		return label

	############################################################################

	def on_tool_selected(self):
		super().on_tool_selected()
		# Usual text entry shortcuts don't work otherwise
		self.set_action_sensitivity('paste', False)
		self.set_action_sensitivity('select_all', False)
		self.set_action_sensitivity('selection_cut', False)
		self.set_action_sensitivity('selection_copy', False)

	def on_tool_unselected(self):
		self.set_action_sensitivity('paste', True)
		self.set_action_sensitivity('select_all', True)
		self.set_action_sensitivity('selection_cut', True)
		self.set_action_sensitivity('selection_copy', True)

	def give_back_control(self, preserve_selection):
		if self.should_cancel:
			self.on_cancel()

	def force_text_tool(self, string):
		self.row.set_active(True)
		self.set_common_values(1)
		self.on_release_on_area(None, None, 100, 100)
		self.set_string(string)

	def set_string(self, string):
		self.entry.get_buffer().set_text(string, -1)

	############################################################################

	def on_press_on_area(self, event, surface, event_x, event_y):
		self.set_common_values(event.button)

	def on_release_on_area(self, event, surface, event_x, event_y):
		self.x_begin = event_x
		self.y_begin = event_y
		self.should_cancel = True

		# TODO use the widget again, and cairo.ToyFontFace
		self.set_font()

		if self.get_option_value('text_italic'):
			self.font_slant = cairo.FontSlant.ITALIC
		else:
			self.font_slant = cairo.FontSlant.NORMAL
		if self.get_option_value('text_bold'):
			self.font_weight = cairo.FontWeight.BOLD
		else:
			self.font_weight = cairo.FontWeight.NORMAL

		if event is None: # TODO l'ouvrir à l'endroit précédent si clic droit ?
			self.open_popover_at(int(event_x), int(event_y))
		else:
			self.open_popover_at(int(event.x), int(event.y))

	def open_popover_at(self, x, y):
		rectangle = Gdk.Rectangle()
		rectangle.x = x
		rectangle.y = y
		rectangle.height = 1
		rectangle.width = 1
		self.popover.set_pointing_to(rectangle)
		self.popover.set_relative_to(self.get_image())
		self.popover.popup()
		self.entry.grab_focus()
		self.preview_text()

	def on_insert_text(self, *args):
		self.popover.popdown()
		if self.has_current_text():
			operation = self.build_operation()
			self.apply_operation(operation)
			self.set_string('')

	def has_current_text(self):
		b = self.entry.get_buffer()
		self.text_string = b.get_text(b.get_start_iter(), b.get_end_iter(), False)
		if self.text_string == '':
			self.restore_pixbuf()
			self.non_destructive_show_modif()
			return False
		else:
			return True

	def preview_text(self, *args):
		if self.has_current_text():
			operation = self.build_operation()
			self.do_tool_operation(operation)

	def on_cancel(self, *args):
		self.restore_pixbuf()
		self.popover.popdown()
		self.set_string('')
		self.should_cancel = False

	############################################################################

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'rgba1': self.main_color,
			'rgba2': self.secondary_color,
			'font_fam': self.font_fam,
			'font_slant': self.font_slant,
			'font_weight': self.font_weight,
			'font_size': self.tool_width,
			'x': self.x_begin,
			'y': self.y_begin,
			'background': self.background_id,
			'text': self.text_string
		}
		return operation

	def do_tool_operation(self, operation):
		super().do_tool_operation(operation)
		cairo_context = cairo.Context(self.get_surface())

		font_fam = operation['font_fam']
		font_slant = operation['font_slant']
		font_weight = operation['font_weight']
		font_size = operation['font_size'] * 3 # XXX totalement arbitraire
		cairo_context.select_font_face(font_fam, font_slant, font_weight)
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
				self.op_bg_rectangle(cairo_context, c2, font_size, i, text_x, \
				                                              text_y, line_text)
			elif operation['background'] == 'shadow':
				self.op_bg_shadow(cairo_context, c2, font_size, text_x, \
				                                              line_y, line_text)
			elif operation['background'] == 'outline':
				self.op_bg_outline(cairo_context, c2, font_size, text_x, \
				                                              line_y, line_text)
			####################################################################
			# Draw text for the line #####################################
			cairo_context.set_source_rgba(c1.red, c1.green, c1.blue, c1.alpha)
			cairo_context.move_to(text_x, line_y)
			cairo_context.show_text( line_text )
			i = i + 1
		self.non_destructive_show_modif()

	def op_bg_shadow(self, context, color, font_size, text_x, text_y, line):
		context.set_source_rgba(color.red, color.green, color.blue, color.alpha)
		dist = max(min(int(font_size/18), 4), 1)
		context.move_to(text_x + dist, text_y + dist)
		context.show_text(line)

	def op_bg_outline(self, context, color, font_size, text_x, text_y, line):
		context.set_source_rgba(color.red, color.green, color.blue, color.alpha)
		dist = max(min(int(font_size/18), 8), 1)
		for dx in range(-dist, dist):
			for dy in range(-dist, dist):
				context.move_to(text_x + dx, text_y + dy)
				context.show_text(line)

	def op_bg_rectangle(self, context, color, font_size, i, text_x, text_y, line):
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

