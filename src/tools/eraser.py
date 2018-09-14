# eraser.py

from gi.repository import Gtk, Gdk, Gio
import cairo

from .tools import ToolTemplate

class ToolEraser(ToolTemplate):
    __gtype_name__ = 'ToolEraser'

    id = 'eraser'
    icon_name = 'edit-delete-symbolic'
    label = _("Eraser")
    use_size = True

    def __init__(self, window, **kwargs):
        super().__init__(window)
        self.past_x = -1
        self.past_y = -1
        self.w_context = None

    def give_back_control(self):
        pass

    def on_key_on_area(self, area, event, surface):
        print("key")

    def on_motion_on_area(self, area, event, surface):
        self.w_context.set_line_cap(cairo.LineCap.ROUND)
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
        # if event.button == 3: # FIXME ? Doesn't work
        #     self.w_context.set_source_rgba(left_color.red, left_color.green, left_color.blue, left_color.alpha)
        # if event.button == 1:
        #     self.w_context.set_source_rgba(right_color.red, right_color.green, right_color.blue, right_color.alpha)
        self.w_context.set_operator(cairo.Operator.CLEAR)

    def on_release_on_area(self, area, event, surface):
        print("release")

        self.x_press = 0.0
        self.y_press = 0.0
        self.past_x = -1
        self.past_y = -1

        self.w_context.set_operator(cairo.Operator.OVER)
        self.window_can_take_back_control = True
