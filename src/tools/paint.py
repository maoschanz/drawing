# TODO still shit

from gi.repository import Gtk, Gdk, Gio, GdkPixbuf
import cairo

from .tools import ToolTemplate
from .tools import get_rgb_for_xy

class ToolPaint(ToolTemplate):
    __gtype_name__ = 'ToolPaint'

    def __init__(self, window, **kwargs):
        super().__init__('paint', _("Paint"), 'edit-clear-all-symbolic', window)
        self.new_color = None
        self.old_color = None

    def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color):
        print("press")
        if event.button == 1:
            self.new_color = left_color
        if event.button == 3:
            self.new_color = right_color

    def on_release_on_area(self, area, event, surface):
        # Guard clause: we can't paint outside of the surface
        if event.x < 0 or event.x > surface.get_width() \
        or event.y < 0 or event.y > surface.get_height():
            return

        print('paint')

        # Cairo doesn't provide methods for what we want to do. I will have to
        # define myself how to decide what should be filled.
        # The heuristic here is that we create a hull containing the area of
        # color we want to paint. We don't care about
        w_context = cairo.Context(surface)

        self.old_color = get_rgb_for_xy(surface, event.x, event.y)
        # self.old_color = self.get_rgb_for_xy(event.x, event.y)

        (x, y) = (int(event.x), int(event.y))
        while (get_rgb_for_xy(surface, x, y) == self.old_color) and y > 0:
        # while (self.get_rgb_for_xy(x, y) == self.old_color) and y > 0:
            y = y - 1
        y = y + 1 # sinon ça crashe ?
        w_context.move_to(x, y)

        (first_x, first_y) = (x, y)

        print(str(x) + ' ' + str(y))

        # 0 1 2
        # 7   3
        # 6 5 4

        direction = 5
        should_stop = False
        i = 0

        x_shift = [-1, 0, 1, 1, 1, 0, -1, -1]
        y_shift = [-1, -1, -1, 0, 1, 1, 1, 0]

        while (not should_stop and i < 50000):
            new_x = -2
            new_y = -2

            end_circle = False

            j = 0
            while (not end_circle) or (j < 8):
                # if (self.get_rgb_for_xy(x+x_shift[direction], y+y_shift[direction]) == self.old_color) \
                if (get_rgb_for_xy(surface, x+x_shift[direction], y+y_shift[direction]) == self.old_color) \
                and (x+x_shift[direction] > 0) \
                and (y+y_shift[direction] > 0) \
                and (x+x_shift[direction] < surface.get_width()) \
                and (y+y_shift[direction] < surface.get_height()-2): # ???
                # if (self.get_rgb_for_xy(x+x_shift[direction], y+y_shift[direction]) == self.old_color):
                # if (get_rgb_for_xy(surface, x+x_shift[direction], y+y_shift[direction]) == self.old_color):
                    new_x = x+x_shift[direction]
                    new_y = y+y_shift[direction]
                    direction = (direction+1) % 8
                elif (x != new_x or y != new_y):
                    x = new_x+x_shift[direction]
                    y = new_y+y_shift[direction]
                    end_circle = True
                else:
                    print('cas emmerdant')
                j = j+1

            direction = (direction+4) % 8
            # print('direction:')
            # print(direction)
            if (new_x != -2):
                w_context.line_to(x, y)
            # else:
            #     print('TENTATIVE ABUSIVE D\'AJOUT')
            #     should_stop = True

            if (i > 10) and (first_x-5 < x < first_x+5) and (first_y-5 < y < first_y+5):
                should_stop = True

            i = i + 1
            # print('----------')

            if i == 2000:
                dialog = Gtk.Dialog(use_header_bar=True, modal=True, transient_for=self.window)
                dialog.add_button(_("Continue"), Gtk.ResponseType.APPLY)
                dialog.add_button(_("Abort"), Gtk.ResponseType.CANCEL)
                dialog.get_content_area().add(Gtk.Label(_( \
"""The area seems poorly delimited, or is very complex.
This tool is not seriously implemented, and may not be able to paint the area.

Do you want to abort the operation, or to let the tool struggle ?""" \
                ), margin=10))
                dialog.show_all()
                result = dialog.run()
                if result == -10:
                    dialog.destroy()
                else:
                    dialog.destroy()
                    return

        w_context.close_path()
        # print('i: ' + str(i))

        w_context.set_source_rgba(self.new_color.red, self.new_color.green, self.new_color.blue, self.new_color.alpha)
        w_context.fill()

        self.apply_to_pixbuf()

    # def get_rgb_for_xy(self, x, y):
    #    # Guard clause: we can't perform color picking outside of the surface
    #     if x < 0 or x > self.surface.get_width() or y < 0 or y > self.surface.get_height():
    #         return [-1,-1,-1]
    #     screenshot = Gdk.pixbuf_get_from_surface(self.surface, float(x), float(y), 1, 1)
    #     rgb_vals = screenshot.get_pixels()
    #     return rgb_vals # array de 3 valeurs, de 0 à 255
