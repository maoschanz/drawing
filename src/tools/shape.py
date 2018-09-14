# shape.py

from gi.repository import Gtk, Gdk, Gio
import cairo
import math

from .tools import ToolTemplate

# FIXME le polygon filled merdoie

class ToolShape(ToolTemplate):
    __gtype_name__ = 'ToolShape'

    id = 'shape'
    icon_name = 'non-starred-symbolic'
    label = _("Shape")
    use_options = True
    window_can_take_back_control = True
    use_size = True
    set_clip = False

    def __init__(self, window, **kwargs):
        super().__init__(window)
        
        self.past_x = -1.0
        self.past_y = -1.0

        # Building the widget containing options
        self.options_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=10)

        shape_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        shape_box.get_style_context().add_class('linked')

        self.shape_btn = Gtk.RadioButton(draw_indicator=False, label=_("Rectangle"))
        self.rounded_btn = Gtk.RadioButton(group=self.shape_btn, draw_indicator=False, label=_("Rounded rectangle"))
        self.ellipsis_btn = Gtk.RadioButton(group=self.shape_btn, draw_indicator=False, label=_("Ellipsis"))
        self.circle_btn = Gtk.RadioButton(group=self.shape_btn, draw_indicator=False, label=_("Circle"))
        self.polygon_btn = Gtk.RadioButton(group=self.shape_btn, draw_indicator=False, label=_("Polygon"))

        self.shape_btn.connect('clicked', self.on_shape_changed)
        self.rounded_btn.connect('clicked', self.on_shape_changed)
        self.ellipsis_btn.connect('clicked', self.on_shape_changed)
        self.circle_btn.connect('clicked', self.on_shape_changed)
        self.polygon_btn.connect('clicked', self.on_shape_changed)

        shape_box.add(self.shape_btn)
        shape_box.add(self.rounded_btn)
        # shape_box.add(self.ellipsis_btn)
        shape_box.add(self.circle_btn)
        shape_box.add(self.polygon_btn)

        style_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        style_box.get_style_context().add_class('linked')

        self.style_empty_btn = Gtk.RadioButton(draw_indicator=False, label=_("Empty"))
        self.style_filled_btn = Gtk.RadioButton(group=self.style_empty_btn, draw_indicator=False, label=_("Filled"))
        self.style_secondary_btn = Gtk.RadioButton(group=self.style_empty_btn, draw_indicator=False, label=_("Filled (secondary color)"))

        self.style_empty_btn.connect('clicked', self.on_style_changed)
        self.style_filled_btn.connect('clicked', self.on_style_changed)
        self.style_secondary_btn.connect('clicked', self.on_style_changed)

        style_box.add(self.style_empty_btn)
        style_box.add(self.style_filled_btn)
        style_box.add(self.style_secondary_btn)

        self.options_box.add(Gtk.Label(label=_("Shape:")))
        self.options_box.add(shape_box)

        self.options_box.add(Gtk.Label(label=_("Style:")))
        self.options_box.add(style_box)

        self.shape_btn.set_active(True)
        self.style_secondary_btn.set_active(True)

        self.selected_shape = self.shape_btn.get_label()
        self.selected_style = self.style_secondary_btn.get_label()

    def on_shape_changed(self, b):
        self.selected_shape = b.get_label()

    def on_style_changed(self, b):
        self.selected_style = b.get_label()

    def get_options_widget(self):
        return self.options_box

    def get_options_label(self):
        return self.selected_shape + ' - ' + self.selected_style

    def give_back_control(self):
        pass

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
        print("release")
        primary_color = ''
        secondary_color = ''
        if event.button == 3:
            primary_color = self.right_color
            secondary_color = self.left_color
        else:
            primary_color = self.left_color
            secondary_color = self.right_color

        w_context = cairo.Context(surface)

        if self.selected_shape == _("Rounded rectangle"):

            # FIXME l'alpha du bon event svp
            pattern = cairo.MeshPattern() # carré arrondi parfait mais refaire les signes
            pattern.begin_patch()
            height = (self.y_press - event.y)/2
            width = -(self.x_press - event.x)/2
            pattern.move_to(event.x-width, event.y)
            pattern.curve_to(event.x-width-width, event.y, event.x-width-width, event.y, event.x-width-width, event.y+height)
            pattern.curve_to(event.x-width-width, event.y+2*height, event.x-width-width, event.y+2*height, event.x-width, event.y+2*height)
            pattern.curve_to(event.x-width+width, event.y+2*height, event.x-width+width, event.y+2*height, event.x-width+width, event.y+height)
            pattern.curve_to(event.x-width+width, event.y, event.x-width+width, event.y, event.x-width, event.y)
            pattern.set_corner_color_rgba(0, self.left_color.red, self.left_color.green, self.left_color.blue, self.left_color.alpha)
            pattern.set_corner_color_rgba(1, 1, 1, 1, self.left_color.alpha) # seul l'alpha semble compter ??
            pattern.set_corner_color_rgba(2, 1, 0, 0, self.left_color.alpha)
            pattern.set_corner_color_rgba(3, 1, 1, 1, self.left_color.alpha)
            pattern.end_patch()

            w_context.mask(pattern)

            self.window_can_take_back_control = True


        elif self.selected_shape == _("Polygon"):

            w_context.set_line_width(self.tool_width)

            if self.past_x == -1.0:
                (self.past_x, self.past_y) = (self.x_press, self.y_press)
                w_context.move_to(self.x_press, self.y_press)
                self.path = w_context.copy_path()
            else:
                w_context.append_path(self.path)

            if (event.x - self.past_x < self.tool_width) and (event.y - self.past_y < self.tool_width):
                print("stroke")
                w_context.close_path()
                if self.selected_style == _("Filled"):
                    w_context.fill()
                elif self.selected_style == _("Filled (secondary color)"):
                    w_context.set_source_rgba(secondary_color.red, secondary_color.green, \
                        secondary_color.blue, secondary_color.alpha)
                    w_context.fill_preserve() # TODO c'est élégant ça, je devrais le faire ailleurs
                    w_context.set_source_rgba(primary_color.red, primary_color.green, \
                        primary_color.blue, primary_color.alpha)
                    w_context.stroke()
                else:
                    w_context.stroke()
                (self.past_x, self.past_y) = (-1.0, -1.0)

                self.window_can_take_back_control = True

            else:
                w_context.line_to(event.x, event.y)
                w_context.stroke_preserve() # draw the line without closing the path
                self.path = w_context.copy_path()

        elif self.selected_shape == _("Ellipsis"):
        # FIXME pas de pattern c'est trop moche go tracer à l'ancienne

            print('ellipsis')

            self.window_can_take_back_control = True

        elif self.selected_shape == _("Circle"):

            rayon = math.sqrt((self.x_press - event.x)*(self.x_press - event.x) \
                + (self.y_press - event.y)*(self.y_press - event.y))

            w_context.set_line_width(self.tool_width)

            if self.selected_style == _("Filled (secondary color)"):
                w_context.new_sub_path()
                w_context.arc(self.x_press, self.y_press, rayon, 0.0, 2*math.pi)
                w_context.set_source_rgba(secondary_color.red, secondary_color.green, \
                    secondary_color.blue, secondary_color.alpha)
                w_context.fill()
                w_context.stroke()
            w_context.set_source_rgba(primary_color.red, primary_color.green, \
                primary_color.blue, primary_color.alpha)

            w_context.new_sub_path()
            w_context.arc(self.x_press, self.y_press, rayon, 0.0, 2*math.pi)
            if self.selected_style == _("Filled"):
                w_context.fill()
            w_context.stroke()

            self.window_can_take_back_control = True

        elif self.selected_shape == _("Rectangle"):

            w_context.set_line_width(self.tool_width)

            if self.selected_style == _("Filled (secondary color)"):
                w_context.move_to(self.x_press, self.y_press)
                w_context.line_to(self.x_press, event.y)
                w_context.line_to(event.x, event.y)
                w_context.line_to(event.x, self.y_press)
                w_context.close_path()
                w_context.set_source_rgba(secondary_color.red, secondary_color.green, \
                    secondary_color.blue, secondary_color.alpha)
                w_context.fill()
                w_context.stroke()
            w_context.set_source_rgba(primary_color.red, primary_color.green, \
                primary_color.blue, primary_color.alpha)

            w_context.move_to(self.x_press, self.y_press)
            w_context.line_to(self.x_press, event.y)
            w_context.line_to(event.x, event.y)
            w_context.line_to(event.x, self.y_press)
            w_context.close_path()

            if self.selected_style == _("Filled"):
                w_context.fill()
            w_context.stroke()

            self.window_can_take_back_control = True

        ############################################

        # pattern = cairo.MeshPattern()
        # pattern.begin_patch()
        # pattern.move_to(event.x, event.y)
        # pattern.curve_to(event.x+30, event.y-30, event.x+60, event.y+30, event.x+100, event.y+0)
        # pattern.curve_to(event.x+60, event.y+30, event.x+130, event.y+60, event.x+100, event.y+100)
        # pattern.curve_to(event.x+60, event.y+70, event.x+30, event.y+130, event.x+0, event.y+100)
        # pattern.curve_to(event.x+30, event.y+70, event.x-30, event.y+30, event.x+0, event.y+0)
        # pattern.set_corner_color_rgba(0, self.left_color.red, self.left_color.green, self.left_color.blue, self.left_color.alpha)
        # pattern.set_corner_color_rgba(1, 1, 1, 1, self.left_color.alpha) # seul l'alpha semble compter ??
        # pattern.set_corner_color_rgba(2, 1, 1, 1, self.left_color.alpha)
        # pattern.set_corner_color_rgba(3, 1, 1, 1, self.left_color.alpha)
        # pattern.end_patch()


        # pattern = cairo.MeshPattern() # losange fixe (vers le haut)
        # pattern.begin_patch()
        # pattern.move_to(event.x, event.y)
        # pattern.line_to(event.x+30, event.y-30)
        # pattern.line_to(event.x, event.y-60)
        # pattern.line_to(event.x-30, event.y-30)
        # pattern.line_to(event.x, event.y)
        # pattern.set_corner_color_rgba(0, self.left_color.red, self.left_color.green, self.left_color.blue, self.left_color.alpha)
        # pattern.set_corner_color_rgba(1, 1, 1, 1, self.left_color.alpha) # seul l'alpha semble compter ??
        # pattern.set_corner_color_rgba(2, 1, 0, 0, self.left_color.alpha)
        # pattern.set_corner_color_rgba(3, 1, 1, 1, self.left_color.alpha)
        # pattern.end_patch()

        # pattern = cairo.MeshPattern()
        # pattern.begin_patch()
        # pattern.move_to(self.x_press, self.y_press)
        # pattern.line_to(event.x, event.y)
        # # length = sqrt((-)*(-))
        # pattern.line_to((self.x_press+event.x)/3, (self.y_press+event.y)/3) # FIXME
        # pattern.set_corner_color_rgba(0, self.left_color.red, self.left_color.green, self.left_color.blue, self.left_color.alpha)
        # pattern.set_corner_color_rgba(1, 1, 1, 1, self.left_color.alpha) # seul l'alpha semble compter ??
        # pattern.set_corner_color_rgba(2, 1, 1, 1, self.left_color.alpha)
        # pattern.end_patch()

        # TODO d'autres formes?

        # w_context.mask(pattern)

        self.x_press = 0.0
        self.y_press = 0.0
        # self.past_x = -1.0
        # self.past_y = -1.0
