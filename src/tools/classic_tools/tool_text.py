# tool_text.py

from gi.repository import Gtk, Gdk
import cairo

from .abstract_tool import ToolTemplate

class ToolText(ToolTemplate):
	__gtype_name__ = 'ToolText'

	def __init__(self, window, **kwargs):
		super().__init__('text', _("Text"), 'tool-text-symbolic', window)

		self.main_color = None
		self.secondary_color = None
		self.x_begin = 0.0
		self.y_begin = 0.0
		self.should_cancel = False

		self.add_tool_action_boolean('text_opaque_bg', False)

		builder = Gtk.Builder().new_from_resource( \
		                  '/com/github/maoschanz/drawing/tools/ui/tool_text.ui')

		# Main popover for text insertion
		self.popover = builder.get_object('insertion-popover')
		self.entry = builder.get_object('entry')
		self.entry.set_size_request(100, 50)
		insert_btn = builder.get_object('insert_btn')
		insert_btn.connect('clicked', self.on_insert_text)
		cancel_btn = builder.get_object('cancel_btn')
		cancel_btn.connect('clicked', self.on_cancel)
		self.entry.get_buffer().connect('changed', self.preview_text)

		# Building the widget containing options
		self.options_box = builder.get_object('options-widget')
		self.font_btn = builder.get_object('font-chooser-widget')
		self.backg_switch = builder.get_object('backg-switch')

		self.font_btn.set_font('Sans 36')
		self.font_fam = self.font_btn.get_font()

	def hide_row_label(self):
		self.label_widget.set_visible(False)

	def show_row_label(self):
		self.label_widget.set_visible(True)

	def on_tool_selected(self):
		# Ctrl+v can't paste text in the entry otherwise
		self.set_action_sensitivity('paste', False)

	def on_tool_unselected(self):
		self.set_action_sensitivity('paste', True)

	def get_options_label(self):
		return self.font_btn.get_font()

	def get_options_widget(self):
		return self.options_box

	def give_back_control(self, preserve_selection):
		if self.should_cancel:
			self.on_cancel()

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color, event_x, event_y):
		if event.button == 1:
			self.main_color = left_color
			self.secondary_color = right_color
		else:
			self.main_color = right_color
			self.secondary_color = left_color

	def on_release_on_area(self, area, event, surface, event_x, event_y):
		self.x_begin = event_x
		self.y_begin = event_y
		self.should_cancel = True

		self.font_fam = self.font_btn.get_font()
		self.font_slant = cairo.FontSlant.NORMAL
		self.font_weight = cairo.FontWeight.NORMAL
		if 'Bold' in self.font_fam:
			self.font_weight = cairo.FontWeight.BOLD
		if 'Regular' in self.font_fam:
			self.font_slant = cairo.FontSlant.NORMAL
			self.font_weight = cairo.FontWeight.NORMAL
		if 'Italic' in self.font_fam:
			self.font_slant = cairo.FontSlant.ITALIC
		if 'Oblique' in self.font_fam:
			self.font_slant = cairo.FontSlant.OBLIQUE

		self.font_fam.replace('Bold', '')
		self.font_fam.replace('Regular', '')
		self.font_fam.replace('Italic', '')
		self.font_fam.replace('Oblique', '')

		self.tool_width = int(self.font_fam.split(' ')[-1])
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
		self.text_string = self.entry.get_buffer().get_text( \
		    self.entry.get_buffer().get_start_iter(), \
		    self.entry.get_buffer().get_end_iter(), False)
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

	def set_string(self, string):
		self.entry.get_buffer().set_text(string, -1)

	def build_operation(self):
		operation = {
			'tool_id': self.id,
			'rgba_main': self.main_color,
			'rgba_secd': self.secondary_color,
			'font_fam': self.font_fam,
			'font_slant': self.font_slant,
			'font_weight': self.font_weight,
			'font_size': self.tool_width,
			'x': self.x_begin,
			'y': self.y_begin,
			'background': self.backg_switch.get_state(),
			'text': self.text_string
		}
		return operation

	def do_tool_operation(self, operation):
		if operation['tool_id'] != self.id:
			return
		self.restore_pixbuf()
		cairo_context = cairo.Context(self.get_surface())

		font_fam = operation['font_fam']
		font_slant = operation['font_slant']
		font_weight = operation['font_weight']
		font_size = operation['font_size']
		cairo_context.select_font_face(font_fam, font_slant, font_weight)
		cairo_context.set_font_size(font_size)

		lines = operation['text'].split('\n')
		i = 0

		main_color = operation['rgba_main']
		secondary_color = operation['rgba_secd']
		text_x = operation['x']
		text_y = operation['y']

		for a_line in lines:
			if operation['background']:
				cairo_context.set_source_rgba(0.0, 0.0, 0.0, 0.0)
				cairo_context.move_to(text_x, text_y + (i+0.2)*font_size)
				cairo_context.show_text( a_line )
				cairo_context.rel_line_to(0, (-1)*font_size)
				cairo_context.line_to(text_x, text_y + (i-0.8)*font_size)
				cairo_context.line_to(text_x, text_y + (i+0.2)*font_size)
				cairo_context.set_source_rgba(secondary_color.red, \
				    secondary_color.green, secondary_color.blue, secondary_color.alpha)
				cairo_context.fill()
				cairo_context.stroke()
			cairo_context.set_source_rgba(main_color.red, main_color.green, \
			                                  main_color.blue, main_color.alpha)
			cairo_context.move_to(text_x, text_y + i*font_size)
			cairo_context.show_text( a_line )
			i = i + 1
		self.non_destructive_show_modif()

