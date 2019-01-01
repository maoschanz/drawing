# text.py

from gi.repository import Gtk, Gdk, Gio
import cairo

from .tools import ToolTemplate

class ToolText(ToolTemplate):
	__gtype_name__ = 'ToolText'

	def __init__(self, window, **kwargs):
		super().__init__('text', _("Text"), 'font-x-generic-symbolic', window)

		self.main_color = None
		self.secondary_color = None
		(self.x_begin, self.y_begin) = (0, 0)
		self.should_cancel = False

		builder = Gtk.Builder()
		builder.add_from_resource("/com/github/maoschanz/Drawing/tools/ui/text.ui")

		# Main popover for text insertion
		self.popover = builder.get_object("insertion-popover")
		self.entry = builder.get_object("entry")
		self.entry.set_size_request(100, 50)
		insert_btn = builder.get_object("insert_btn")
		insert_btn.connect('clicked', self.on_insert_text)
		cancel_btn = builder.get_object("cancel_btn")
		cancel_btn.connect('clicked', self.on_cancel)
		self.entry.get_buffer().connect('changed', self.preview_text)

		# Building the widget containing options
		self.options_box = builder.get_object("options-menu")
		self.font_btn = builder.get_object("font-btn")
		self.backg_switch = builder.get_object("backg-switch")

	def hide_row_label(self):
		self.label_widget.set_visible(False)

	def show_row_label(self):
		self.label_widget.set_visible(True)

	def get_options_label(self):
		return self.font_btn.get_font()

	# def get_options_model(self): # FIXME !!
	# 	return self.options_menu_model

	def give_back_control(self):
		if self.should_cancel:
			self.on_cancel()
			return True
		else:
			return False

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color):
		if event.button == 1:
			self.main_color = left_color
			self.secondary_color = right_color
		if event.button == 3:
			self.main_color = right_color
			self.secondary_color = left_color

	def on_release_on_area(self, area, event, surface):
		(self.x_begin, self.y_begin) = (event.x, event.y)
		self.should_cancel = True

		self.font_fam = self.font_btn.get_font()
		self.slant = cairo.FontSlant.NORMAL
		self.weight = cairo.FontWeight.NORMAL
		if 'Bold' in self.font_fam:
			self.weight = cairo.FontWeight.BOLD
		if 'Regular' in self.font_fam:
			self.slant = cairo.FontSlant.NORMAL
			self.weight = cairo.FontWeight.NORMAL
		if 'Italic' in self.font_fam:
			self.slant = cairo.FontSlant.ITALIC
		if 'Oblique' in self.font_fam:
			self.slant = cairo.FontSlant.OBLIQUE

		self.font_fam.replace('Bold', '')
		self.font_fam.replace('Regular', '')
		self.font_fam.replace('Italic', '')
		self.font_fam.replace('Oblique', '')

		self.tool_width = int(self.font_fam.split(' ')[-1])

		rectangle = Gdk.Rectangle()
		rectangle.x = int(event.x)
		rectangle.y = int(event.y)
		rectangle.height = 1
		rectangle.width = 1
		self.popover.set_pointing_to(rectangle)
		self.popover.set_relative_to(area)
		self.popover.popup()
		self.entry.grab_focus()
		self.preview_text()

	def on_insert_text(self, *args):
		self.preview_text()
		self.popover.popdown()
		self.apply_to_pixbuf()
		self.entry.get_buffer().set_text('', 0)

	def preview_text(self, *args):
		text = self.entry.get_buffer().get_text( self.entry.get_buffer().get_start_iter(), \
			self.entry.get_buffer().get_end_iter(), False)
		if text == '':
			return
		self.restore_pixbuf()

		w_context = cairo.Context(self.window.get_surface())
		w_context.set_source_rgba(self.main_color.red, self.main_color.green, \
			self.main_color.blue, self.main_color.alpha)
		w_context.select_font_face(self.font_fam, self.slant, self.weight)
		w_context.set_font_size(self.tool_width)

		lines = text.split('\n')
		i = 0
		for a_line in lines:
			print(a_line)
			print(self.tool_width)
			if self.backg_switch.get_state():
				w_context.set_source_rgba(self.secondary_color.red, self.secondary_color.green, \
					self.secondary_color.blue, 0.0)
				w_context.move_to(self.x_begin, self.y_begin + (i+0.2)*self.tool_width)
				w_context.show_text( a_line )
				w_context.rel_line_to(0, (-1)*self.tool_width)
				w_context.line_to(self.x_begin, self.y_begin + (i-0.8)*self.tool_width)
				w_context.line_to(self.x_begin, self.y_begin + (i+0.2)*self.tool_width)
				w_context.set_source_rgba(self.secondary_color.red, self.secondary_color.green, \
					self.secondary_color.blue, self.secondary_color.alpha)
				w_context.fill()
				w_context.stroke()
			w_context.set_source_rgba(self.main_color.red, self.main_color.green, \
				self.main_color.blue, self.main_color.alpha)
			w_context.move_to(self.x_begin, self.y_begin + i*self.tool_width)
			w_context.show_text( a_line )
			i = i + 1
		self.non_destructive_show_modif()

	def on_cancel(self, *args):
		self.restore_pixbuf()
		self.popover.popdown()
		self.entry.get_buffer().set_text('', 0)
		self.should_cancel = False

