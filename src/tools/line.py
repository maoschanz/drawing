# line.py

from gi.repository import Gtk, Gdk, Gio
import cairo

from .tools import build_row

class ToolLine():
    __gtype_name__ = 'ToolLine'

    id = 'line'
    icon_name = 'list-remove-symbolic'
    label = _("Line")
    use_options = True
    window_can_take_back_control = True
    use_size = True
    set_clip = False

    def __init__(self, window, **kwargs):
        self.tool_width = 20
        build_row(self)
        self._window = window

        # Building the widget containing options
        self.options_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=10)

        self.options_box.add(Gtk.Label(label=_("Line type:")))
        curv_btn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        curv_btn_box.get_style_context().add_class('linked')

        c_radio_btn = Gtk.RadioButton(draw_indicator=False, label=_("Straight"))
        c_radio_btn2 = Gtk.RadioButton(group=c_radio_btn, draw_indicator=False, label=_("Arc"))
        c_radio_btn4 = Gtk.RadioButton(group=c_radio_btn, draw_indicator=False, label=_("Arrow"))
        c_radio_btn.connect('clicked', self.on_type_changed)
        c_radio_btn2.connect('clicked', self.on_type_changed)
        c_radio_btn4.connect('clicked', self.on_type_changed)

        curv_btn_box.add(c_radio_btn)
        curv_btn_box.add(c_radio_btn2)
        # curv_btn_box.add(c_radio_btn4)

        self.options_box.add(curv_btn_box)

        self.options_box.add(Gtk.Label(label=_("Line end shape:")))
        end_btn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        end_btn_box.get_style_context().add_class('linked')

        radio_btn = Gtk.RadioButton(draw_indicator=False, label=_("None"))
        radio_btn2 = Gtk.RadioButton(group=radio_btn, draw_indicator=False, label=_("Round"))
        radio_btn3 = Gtk.RadioButton(group=radio_btn, draw_indicator=False, label=_("Square"))

        radio_btn.connect('clicked', self.on_end_changed)
        radio_btn2.connect('clicked', self.on_end_changed)
        radio_btn3.connect('clicked', self.on_end_changed)

        end_btn_box.add(radio_btn)
        end_btn_box.add(radio_btn2)
        end_btn_box.add(radio_btn3)

        self.options_box.add(end_btn_box)

        # Options par défaut
        c_radio_btn.set_active(True)
        radio_btn2.set_active(True)
        self.selected_shape_label = _("Round")
        self.selected_curv_label = _("Straight")
        self.selected_shape_id = cairo.LineCap.ROUND
        self.wait_points = (-1.0, -1.0, -1.0, -1.0)

    def on_end_changed(self, b):
        self.selected_shape_label = b.get_label()
        if self.selected_shape_label == _("None"):
            self.selected_shape_id = cairo.LineCap.BUTT
        elif self.selected_shape_label == _("Round"):
            self.selected_shape_id = cairo.LineCap.ROUND
        elif self.selected_shape_label == _("Square"):
            self.selected_shape_id = cairo.LineCap.SQUARE

    def on_type_changed(self, b):
        self.selected_curv_label = b.get_label()
        self.wait_points = (-1.0, -1.0, -1.0, -1.0)

    def get_options_widget(self):
        return self.options_box

    def get_options_label(self):
        return self.selected_curv_label + ' - ' + self.selected_shape_label

    def give_back_control(self):
        self.wait_points = (-1.0, -1.0, -1.0, -1.0)
        self.x_press = 0.0
        self.y_press = 0.0

    def on_key_on_area(self, area, event, surface):
        print("key")

    def on_motion_on_area(self, area, event, surface):
        pass

    def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color):
        print("press")
        self.window_can_take_back_control = False
        self.x_press = event.x
        self.y_press = event.y
        self.tool_width = tool_width
        self.left_color = left_color
        self.right_color = right_color

    def on_release_on_area(self, area, event, surface):

        w_context = cairo.Context(surface)
        if event.button == 1:
            w_context.set_source_rgba(self.left_color.red, self.left_color.green, \
                 self.left_color.blue, self.left_color.alpha)
        if event.button == 3:
            w_context.set_source_rgba(self.right_color.red, self.right_color.green, \
                self.right_color.blue, self.right_color.alpha)

        if self.selected_curv_label == _("Straight"):

            w_context.set_line_cap(self.selected_shape_id)
            w_context.set_line_width(self.tool_width)
            w_context.move_to(self.x_press, self.y_press)
            w_context.line_to(event.x, event.y)
            w_context.stroke()

            self.window_can_take_back_control = True

        elif self.selected_curv_label == _("Arc"):

            w_context.set_line_cap(self.selected_shape_id)

            # FIXME si self.x_press, self.y_press est trop proche de event.x, event.y
            # il va falloir gérer autrement pour avoir un bézier à un point de contrôle
            # (sans le move_to donc, comme le prévoit la doc)

            if self.wait_points == (-1.0, -1.0, -1.0, -1.0):
                self.wait_points = (self.x_press, self.y_press, event.x, event.y)
            else:
                w_context.move_to(self.wait_points[0], self.wait_points[1])
                w_context.set_line_width(self.tool_width)
                w_context.curve_to(self.wait_points[2], self.wait_points[3], self.x_press, self.y_press, event.x, event.y)
                w_context.stroke()
                self.wait_points = (-1.0, -1.0, -1.0, -1.0)

                self.window_can_take_back_control = True

        elif self.selected_curv_label == _("Arrow"):

            print("arrow")
            self.window_can_take_back_control = True

        self.x_press = 0.0
        self.y_press = 0.0
