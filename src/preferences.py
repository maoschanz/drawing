from gi.repository import Gtk, Gio, GLib, Gdk
from .gi_composites import GtkTemplate

SETTINGS_SCHEMA = 'com.github.maoschanz.Draw'

@GtkTemplate(ui='/com/github/maoschanz/Draw/ui/preferences.ui')
class DrawPrefsWindow(Gtk.Window):
    __gtype_name__ = 'DrawPrefsWindow'

    header_bar = GtkTemplate.Child()
    reset_button = GtkTemplate.Child()
    list_box = GtkTemplate.Child()

    color_edit_switch = GtkTemplate.Child()

    default_backg_button = GtkTemplate.Child()

    experimental_switch = GtkTemplate.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init_template()
        self.list_box.set_selection_mode(Gtk.SelectionMode.NONE)

        self._settings = Gio.Settings.new(SETTINGS_SCHEMA)

        self.color_edit_switch.set_active(not self._settings.get_boolean('direct-color-edit'))
        self.color_edit_switch.connect('notify::active', self.on_color_edit_changed)

        r = float(self._settings.get_strv('default-rgba')[0])
        g = float(self._settings.get_strv('default-rgba')[1])
        b = float(self._settings.get_strv('default-rgba')[2])
        a = float(self._settings.get_strv('default-rgba')[3])
        color = Gdk.RGBA(red=r, green=g, blue=b, alpha=a)
        self.default_backg_button.set_rgba(color)
        self.default_backg_button.connect('color-set', self.on_default_backg_changed)

        self.experimental_switch.set_active(self._settings.get_boolean('experimental'))
        self.experimental_switch.connect('notify::active', self.on_experimental_changed)


# TODO :
# le reset
# idées de paramètres :
# - taille par défaut des nouveau trucs ? (int, int)
# -
# -

    def on_color_edit_changed(self, w, a):
        self._settings.set_boolean('direct-color-edit', not w.get_active())

    def on_experimental_changed(self, w, a):
        self._settings.set_boolean('experimental', w.get_active())

    def on_default_backg_changed(self, w):
        color = self.default_backg_button.get_rgba()
        self._settings.set_strv('default-rgba', [str(color.red), str(color.green), \
            str(color.blue), str(color.alpha)])                                
                
        
