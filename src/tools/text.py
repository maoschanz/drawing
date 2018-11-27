# text.py

from gi.repository import Gtk, Gdk, Gio
import cairo

from .tools import ToolTemplate

class ToolText(ToolTemplate):
    __gtype_name__ = 'ToolText'

    use_options = True
    use_size = True

    def __init__(self, window, **kwargs):
        super().__init__('text', _("Text"), 'font-x-generic-symbolic', window)

        self.primary_color = None
        self.secondary_color = None
        (self.x_begin, self.y_begin) = (0, 0)

        # Main popover for text insertion
        self.popover = Gtk.Popover()
        self.entry = Gtk.TextView() # TODO autres boutons
        self.entry.set_size_request(100, 50)
        self.entry.set_accepts_tab(False)
        cancel_btn = Gtk.Button(image=Gtk.Image(icon_name='window-close-symbolic', \
            icon_size=Gtk.IconSize.BUTTON), tooltip_text=_("Cancel"))
        insert_btn = Gtk.Button(image=Gtk.Image(icon_name='insert-text-symbolic', \
            icon_size=Gtk.IconSize.BUTTON), tooltip_text=_("Insert text here"))
        insert_btn.get_style_context().add_class('suggested-action')
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin=2, spacing=2)
        box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, homogeneous=True)
        box2.get_style_context().add_class('linked')
        frame = Gtk.Frame()
        frame.add(self.entry)
        box.add(frame)
        box2.add(insert_btn)
        box2.add(cancel_btn)
        box.add(box2)
        self.popover.add(box)
        insert_btn.connect('clicked', self.on_insert_text)
        cancel_btn.connect('clicked', self.on_cancel)
        self.entry.get_buffer().connect('changed', self.preview_text)

        # Building the widget containing options
        self.options_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=10)

        backg_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        backg_box.pack_start(Gtk.Label(label=_("Opaque background")), expand=False, fill=False, padding=0)
        self.backg_switch = Gtk.Switch()
        backg_box.pack_end(self.backg_switch, expand=False, fill=False, padding=0)

        self.font_btn = Gtk.FontButton()
        self.font_btn.set_show_size(False)

        self.options_box.add(self.font_btn)
        self.options_box.add(backg_box)

    def get_row(self):
        return self.row

    def hide_row_label(self):
        self.label_widget.set_visible(False)

    def show_row_label(self):
        self.label_widget.set_visible(True)

    def get_options_label(self):
        font_name = self.font_btn.get_font()
        taille = font_name.split(' ')[-1]
        font_name = font_name.replace(taille, '')
        return font_name

    def get_options_widget(self):
        return self.options_box

    def give_back_control(self):
        self.on_cancel(None)

    def on_key_on_area(self, area, event, surface):
        print("key")

    def on_motion_on_area(self, area, event, surface):
        pass

    def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color):
        print("press")
        self.tool_width = int(tool_width)
        self.window_can_take_back_control = False
        if event.button == 1:
            self.primary_color = left_color
            self.secondary_color = right_color
        if event.button == 3:
            self.primary_color = right_color
            self.secondary_color = left_color

    def on_release_on_area(self, area, event, surface):
        print("release")
        (self.x_begin, self.y_begin) = (event.x, event.y)

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

        rectangle = Gdk.Rectangle()
        rectangle.x = int(event.x)
        rectangle.y = int(event.y)
        rectangle.height = 1
        rectangle.width = 1
        self.popover.set_pointing_to(rectangle)
        self.popover.set_relative_to(area)
        self.popover.show_all()
        self.preview_text(None)

    def preview_text(self, *args):
        text = self.entry.get_buffer().get_text( self.entry.get_buffer().get_start_iter(), \
            self.entry.get_buffer().get_end_iter(), False)
        if text == '':
            return
        self.window.use_stable_pixbuf()
        self.w_context = cairo.Context(self.window._surface)

        self.w_context.set_source_rgba(self.primary_color.red, self.primary_color.green, \
            self.primary_color.blue, self.primary_color.alpha)
        self.add_text_from_buffer()

    def on_insert_text(self, b):
        self.preview_text()
        self.popover.popdown()
        self.window.set_stable_pixbuf()
        self.entry.get_buffer().set_text('', 0)
        self.window_can_take_back_control = True

    def add_text_from_buffer(self):
        self.w_context = cairo.Context(self.window._surface)

        self.w_context.select_font_face(self.font_fam, self.slant, self.weight)
        self.w_context.set_font_size(3*self.tool_width)

        text = self.entry.get_buffer().get_text( self.entry.get_buffer().get_start_iter(), \
            self.entry.get_buffer().get_end_iter(), False)
        lines = text.split('\n')
        i = 0
        for a_line in lines:
            if self.backg_switch.get_state():
                self.w_context.set_source_rgba(self.secondary_color.red, self.secondary_color.green, \
                    self.secondary_color.blue, 0.0)
                self.w_context.move_to(self.x_begin, self.y_begin + (i*3+0.5)*self.tool_width)
                self.w_context.show_text( a_line )
                self.w_context.rel_line_to(0, (-3)*self.tool_width)
                self.w_context.line_to(self.x_begin, self.y_begin + (i*3-2.5)*self.tool_width)
                self.w_context.line_to(self.x_begin, self.y_begin + (i*3+0.5)*self.tool_width)
                self.w_context.set_source_rgba(self.secondary_color.red, self.secondary_color.green, \
                    self.secondary_color.blue, self.secondary_color.alpha)
                self.w_context.fill()
                self.w_context.stroke()
            self.w_context.set_source_rgba(self.primary_color.red, self.primary_color.green, \
                self.primary_color.blue, self.primary_color.alpha)
            self.w_context.move_to(self.x_begin, self.y_begin + i*3*self.tool_width)
            self.w_context.show_text( a_line )
            i = i + 1
        self.window.drawing_area.queue_draw()

    def on_cancel(self, b):
        self.window.use_stable_pixbuf()
        self.popover.popdown()
        self.window_can_take_back_control = True
        self.entry.get_buffer().set_text('', 0)
        print('cancelled')
