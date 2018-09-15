# select.py

from gi.repository import Gtk, Gdk, Gio
import cairo

from .tools import ToolTemplate

MENU_XML = """
<?xml version="1.0" encoding="UTF-8"?>
<interface domain="draw">
  <menu id="right-click-menu">
    <section>
        <item>
            <attribute name="label" translatable="yes">Properties</attribute>
            <attribute name="action">win.properties</attribute>
        </item>
    </section>
    <section>
        <item>
            <attribute name="label" translatable="yes">Select all</attribute>
            <attribute name="action">win.select_all</attribute>
        </item>
        <item>
            <attribute name="label" translatable="yes">Unselect</attribute>
            <attribute name="action">win.unselect</attribute>
        </item>
    </section>
    <section>
        <item>
            <attribute name="label" translatable="yes">Import</attribute>
            <attribute name="action">win.import</attribute>
        </item>
        <item>
            <attribute name="label" translatable="yes">Paste</attribute>
            <attribute name="action">win.paste</attribute>
        </item>
    </section>
  </menu>
</interface>
"""

class ToolSelect(ToolTemplate):
    __gtype_name__ = 'ToolSelect'

    id = 'select'
    icon_name = 'edit-select-symbolic'
    label = _("Selection")
    use_options = False # TODO
    set_clip = True

    def __init__(self, window, **kwargs):
        super().__init__(window)

        self.x_press = 0.0
        self.y_press = 0.0
        self.past_x = [-1, -1]
        self.past_y = [-1, -1]

        self.selection_popover = Gtk.Popover()

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5, margin=5)
        box1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box1.get_style_context().add_class('linked')
        box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box2.get_style_context().add_class('linked')

        cut_btn = Gtk.Button(image=Gtk.Image(icon_name='edit-cut-symbolic', icon_size=Gtk.IconSize.BUTTON), \
            tooltip_text=_("Cut"))
        copy_btn = Gtk.Button(image=Gtk.Image(icon_name='edit-copy-symbolic', icon_size=Gtk.IconSize.BUTTON), \
            tooltip_text=_("Copy"))
        delete_btn = Gtk.Button(image=Gtk.Image(icon_name='edit-delete-symbolic', icon_size=Gtk.IconSize.BUTTON), \
            tooltip_text=_("Delete"))
        scale_btn = Gtk.Button(image=Gtk.Image(icon_name='view-restore-symbolic', icon_size=Gtk.IconSize.BUTTON), expand=True, \
            tooltip_text=_("Resize"))
        rotate_btn = Gtk.Button(image=Gtk.Image(icon_name='view-refresh-symbolic', icon_size=Gtk.IconSize.BUTTON), expand=True, \
            tooltip_text=_("Rotate"))
        # TODO exporter la sélection ?

        cut_btn.connect('clicked', self.cancel_selection)
        copy_btn.connect('clicked', self.copy_selection)
        delete_btn.connect('clicked', self.delete_selection)
        scale_btn.connect('clicked', self.cancel_selection)
        rotate_btn.connect('clicked', self.cancel_selection)

        box1.add(cut_btn)
        box1.add(copy_btn)
        box1.add(delete_btn)
        box2.add(scale_btn)
        box2.add(rotate_btn)
        box.add(box1)
        box.add(box2)

        self.selection_popover.add(box)

        builder = Gtk.Builder.new_from_string(MENU_XML, -1)
        menu = builder.get_object("right-click-menu")
        self.rightc_popover = Gtk.Popover.new_from_model(self.window.drawing_area, menu)

        #############################

        # Building the widget containing options
        self.options_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin=10)

        self.options_box.add(Gtk.Label(label=_("Selection type:")))
        btn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        btn_box.get_style_context().add_class('linked')

        radio_btn = Gtk.RadioButton(draw_indicator=False, label=_("Rectangle"))
        radio_btn2 = Gtk.RadioButton(group=radio_btn, draw_indicator=False, label=_("Freehand"))
        radio_btn3 = Gtk.RadioButton(group=radio_btn, draw_indicator=False, label=_("Same color"))

        radio_btn.connect('clicked', self.on_option_changed)
        radio_btn2.connect('clicked', self.on_option_changed)
        radio_btn3.connect('clicked', self.on_option_changed)

        btn_box.add(radio_btn)
        btn_box.add(radio_btn2)
        btn_box.add(radio_btn3)

        radio_btn.set_active(True)

        self.selected_type_label = _("Rectangle")

        self.options_box.add(btn_box)

        self.w_context = None

    def get_row(self):
        return self.row

    def on_option_changed(self, b):
        self.selected_type_label = b.get_label()

    def get_options_widget(self):
        return self.options_box

    def get_options_label(self):
        return self.selected_type_label

    def give_back_control(self):
        self.cancel_selection(None)

    def on_key_on_area(self, area, event, surface):
        print("key")
        # TODO
        # secondary_color = self.right_color
        # self.w_context.set_source_rgba(secondary_color.red, secondary_color.green, \
        #     secondary_color.blue, secondary_color.alpha)
        # self.w_context.paint()

    def on_motion_on_area(self, area, event, surface):
        pass

    def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color):
        print("press")
        self.window_can_take_back_control = False
        area.grab_focus()

        self.w_context = cairo.Context(surface)
        self.w_context.reset_clip()

        self.x_press = event.x
        self.y_press = event.y
        self.left_color = left_color
        self.right_color = right_color

    def on_release_on_area(self, area, event, surface):
        print("release") # TODO à main levée c'est juste un crayon avec close_path() après
        primary_color = ''
        secondary_color = ''
        if event.button == 3:
            if ((self.x_press > self.past_x[0] and self.x_press < self.past_x[1]) \
            or (self.x_press < self.past_x[0] and self.x_press > self.past_x[1])) \
            and ((self.y_press > self.past_y[0] and self.y_press < self.past_y[1]) \
            or (self.y_press < self.past_y[0] and self.y_press > self.past_y[1])):
                self.selection_popover.show_all()
            else:
                rectangle = Gdk.Rectangle()
                rectangle.x = int(event.x)
                rectangle.y = int(event.y)
                rectangle.height = 1
                rectangle.width = 1
                self.rightc_popover.set_pointing_to(rectangle)
                self.rightc_popover.set_relative_to(area)
                self.rightc_popover.show_all()
            return
        else:
            # If nothing is selected (only -1), coordinates should be memorized, but
            # if something is already selected, the selection should be canceled (the
            # action is performed outside of the current selection), or stay the same
            # (the user is moving the selection by dragging it).
            if self.past_x[0] == -1:
                self.past_x[0] = event.x
                self.past_x[1] = self.x_press
                self.past_y[0] = event.y
                self.past_y[1] = self.y_press
                print('cas -1, on continue la fonction')

                rectangle = Gdk.Rectangle()
                rectangle.x = int((self.past_x[0] + self.past_x[1])/2)
                rectangle.y = int((self.past_y[0] + self.past_y[1])/2)
                rectangle.height = 1
                rectangle.width = 1
                self.selection_popover.set_pointing_to(rectangle)
                self.selection_popover.set_relative_to(area)

                self.draw_selection_area()

            elif ((self.x_press > self.past_x[0] and self.x_press < self.past_x[1]) \
            or (self.x_press < self.past_x[0] and self.x_press > self.past_x[1])) \
            and ((self.y_press > self.past_y[0] and self.y_press < self.past_y[1]) \
            or (self.y_press < self.past_y[0] and self.y_press > self.past_y[1])):
                print('cas où faut bouger')
                self.drag_to()
                return
            else:
                print('cas autre')
                self.cancel_selection(None)
                return

    def draw_selection_area(self):

        self.w_context.move_to(self.past_x[1], self.past_y[1])
        self.w_context.line_to(self.past_x[1], self.past_y[0])
        self.w_context.line_to(self.past_x[0], self.past_y[0])
        self.w_context.line_to(self.past_x[0], self.past_y[1])
        self.w_context.close_path()

        self.w_context.clip_preserve()

        self.w_context.set_source_rgba(0.1, 0.1, 0.2, 0.2)

        self.w_context.paint()
        self.w_context.stroke()

        # w_context.scale(0.3, 0.5)
        # w_context.stroke()
        # w_context.rotate(2.0)
        # self.w_context.paint()

        # self.selection_popover.popup()
        self.selection_popover.show_all()

    def delete_selection(self, b):
        self.selection_popover.popdown()
        self.window.pre_modification()

        w_context = cairo.Context(self.window._surface)
        w_context.move_to(self.past_x[0], self.past_y[0])
        w_context.line_to(self.past_x[0], self.past_y[1])
        w_context.line_to(self.past_x[1], self.past_y[1])
        w_context.line_to(self.past_x[1], self.past_y[0])
        w_context.close_path()
        w_context.clip()
        w_context.set_operator(cairo.Operator.CLEAR)
        w_context.paint()
        w_context.set_operator(cairo.Operator.OVER)

        self.window_can_take_back_control = True
        self.window.post_modification()

        self.x_press = 0.0
        self.y_press = 0.0
        self.past_x = [-1, -1]
        self.past_y = [-1, -1]

    def copy_selection(self, b):
        self.selection_popover.popdown()
        self.window.pre_modification()

        print('copy') # TODO

        # on peut faire cairo.Region.copy() ?

        self.window_can_take_back_control = True
        # self.window.post_modification()

        self.x_press = 0.0
        self.y_press = 0.0
        self.past_x = [-1, -1]
        self.past_y = [-1, -1]

    def cancel_selection(self, b):
        self.selection_popover.popdown()
        self.window.pre_modification()

        print('cancel')

        self.window_can_take_back_control = True

        self.x_press = 0.0
        self.y_press = 0.0
        self.past_x = [-1, -1]
        self.past_y = [-1, -1]

    def drag_to(self):
        print('dragging')
        self.window.pre_modification()

        # TODO copier le truc en interne dans DrawImage


        # facile à faire : supprimer l'ancien truc
        w_context = cairo.Context(self.window._surface)
        w_context.move_to(self.past_x[0], self.past_y[0])
        w_context.line_to(self.past_x[0], self.past_y[1])
        w_context.line_to(self.past_x[1], self.past_y[1])
        w_context.line_to(self.past_x[1], self.past_y[0])
        w_context.close_path()
        w_context.clip()
        w_context.set_operator(cairo.Operator.CLEAR)
        w_context.paint()
        w_context.set_operator(cairo.Operator.OVER)

        # TODO mettre en place le truc




        # self.window.post_modification()

        self.x_press = 0.0
        self.y_press = 0.0
        self.past_x = [-2, -2] # TODO remettre des coordonnées
        self.past_y = [-2, -2] # TODO remettre des coordonnées
                
    def get_clip_path():
        print('todo')
