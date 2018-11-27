# picker.py

from gi.repository import Gtk, Gdk, Gio
import cairo

from .tools import ToolTemplate
from .tools import get_rgb_for_xy

class ToolPicker(ToolTemplate):
    __gtype_name__ = 'ToolPicker'

    def __init__(self, window, **kwargs):
        super().__init__('picker', _("Color Picker"), 'color-select-symbolic', window)

    def give_back_control(self):
        pass

    def on_key_on_area(self, area, event, surface):
        print("key")

    def on_motion_on_area(self, area, event, surface):
        pass

    def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color):
        pass

    def on_release_on_area(self, area, event, surface):
        rgb_vals = get_rgb_for_xy(surface, event.x, event.y)
        if rgb_vals == [-1, -1, -1]:
            return # click outside of the surface
        color = Gdk.RGBA(red=rgb_vals[0]/255, green=rgb_vals[1]/255, blue=rgb_vals[2]/255)
        color.alpha = 1.0
        if event.button == 3:
            self.window.color_btn_r.set_rgba(color)
        elif event.button == 1:
            self.window.color_btn_l.set_rgba(color)
