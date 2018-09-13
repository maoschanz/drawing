# pencil.py

from gi.repository import Gtk, Gdk, Gio
import cairo

from .tools import build_row

class ToolPencil():
    __gtype_name__ = 'ToolPencil'

    id = 'pencil'
    icon_name = 'document-edit-symbolic'
    label = _("Pencil")
    use_options = True
    window_can_take_back_control = True
    use_size = True
    set_clip = False

    def __init__(self, window, **kwargs):
        self.tool_width = 20
        self.past_x = -1
        self.past_y = -1
        self.w_context = None
        build_row(self)
        self._window = window

        # Building the widget containing options
        self.options_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=10)
        self.options_box.add(Gtk.Label(label=_("Lead shape:"))) # FIXME pas exactement mdr
        btn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        btn_box.get_style_context().add_class('linked')

        radio_btn = Gtk.RadioButton(draw_indicator=False, label=_("Thin"))
        radio_btn2 = Gtk.RadioButton(group=radio_btn, draw_indicator=False, label=_("Round"))
        radio_btn3 = Gtk.RadioButton(group=radio_btn, draw_indicator=False, label=_("Square"))

        radio_btn.connect('clicked', self.on_option_changed)
        radio_btn2.connect('clicked', self.on_option_changed)
        radio_btn3.connect('clicked', self.on_option_changed)

        btn_box.add(radio_btn)
        btn_box.add(radio_btn2)
        btn_box.add(radio_btn3)

        radio_btn2.set_active(True)

        self.selected_shape_label = _("Round")
        self.selected_shape_id = cairo.LineCap.ROUND

        self.options_box.add(btn_box)

    def on_option_changed(self, b):
        self.selected_shape_label = b.get_label()
        print(self.selected_shape_label)
        if self.selected_shape_label == _("Thin"):
            self.selected_shape_id = cairo.LineCap.BUTT
        elif self.selected_shape_label == _("Round"):
            self.selected_shape_id = cairo.LineCap.ROUND
        elif self.selected_shape_label == _("Square"):
            self.selected_shape_id = cairo.LineCap.SQUARE

    def get_options_widget(self):
        return self.options_box

    def get_options_label(self):
        return self.selected_shape_label

    def give_back_control(self):
        pass

    def on_key_on_area(self, area, event, surface):
        print("key")

    def on_motion_on_area(self, area, event, surface):
        self.w_context.set_line_cap(self.selected_shape_id)
        self.w_context.set_line_width(self.tool_width)
        if (self.past_x > 0):
            self.w_context.move_to(self.past_x, self.past_y)
        self.w_context.line_to(event.x, event.y)
        self.past_x = event.x
        self.past_y = event.y
        self.w_context.stroke()

    def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color):
        print("press")
        self.window_can_take_back_control = False
        self.x_press = event.x
        self.y_press = event.y
        self.tool_width = tool_width
        self.w_context = cairo.Context(surface)
        if event.button == 1:
            self.w_context.set_source_rgba(left_color.red, left_color.green, left_color.blue, left_color.alpha)
        if event.button == 3:
            self.w_context.set_source_rgba(right_color.red, right_color.green, right_color.blue, right_color.alpha)

    def on_release_on_area(self, area, event, surface):
        print("release")

        self.x_press = 0.0
        self.y_press = 0.0
        self.past_x = -1
        self.past_y = -1

        self.window_can_take_back_control = True
