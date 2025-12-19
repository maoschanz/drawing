# tool_brush.py
#
# Copyright 2018-2023 Romain F. T.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Gdk, Gtk
from .abstract_classic_tool import AbstractClassicTool

from .brush_simple import BrushSimple
from .brush_airbrush import BrushAirbrush
from .brush_nib import BrushNib
from .brush_hairy import BrushHairy

class ToolBrush(AbstractClassicTool):
    __gtype_name__ = 'ToolBrush'

    def __init__(self, window, **kwargs):
        super().__init__('brush', _("Brush"), 'tool-brush-symbolic', window)
        self.use_operator = True
        self._used_pressure = False

        self._brushes_dict = {
            'simple': BrushSimple('simple', self),
            'airbrush': BrushAirbrush('airbrush', self),
            'calligraphic': BrushNib('calligraphic', self),
            'hairy': BrushHairy('hairy', self),
        }

        self._brush_type = 'simple'
        self._brush_dir = 'right'
        self.add_tool_action_enum('brush-type', self._brush_type)
        self.add_tool_action_enum('brush-dir', self._brush_dir)
        """
        # custom
        self.stylus_gesture=Gtk.GestureStylus.new(window)
        self.stylus_gesture.connect("down",      self.on_stylus_down)
        self.stylus_gesture.connect("motion",    self.on_stylus_motion)
        self.stylus_gesture.connect("proximity", self.on_stylus_proximity)
        self.stylus_gesture.connect("up",        self.on_stylus_up)
        """

        print("Brush tool initialized")

    def get_options_label(self):
        return _("Brush options")

    def get_editing_tips(self):
        active_brush = self._brushes_dict[self._brush_type]
        return active_brush._get_tips(self._used_pressure, self._brush_dir)

    def on_options_changed(self):
        super().on_options_changed()
        self._brush_type = self.get_option_value('brush-type')
        self._brush_dir = self.get_option_value('brush-dir')

        enable_direction = self._brush_type == 'calligraphic'
        self.set_action_sensitivity('brush-dir', enable_direction)
        # refreshing the rendered operation isn't pertinent

    ############################################################################

    def on_press_on_area(self, event, surface, event_x, event_y):
        self.set_common_values(event.button, event_x, event_y)
        self._manual_path = []
        self._add_pressured_point(event_x, event_y, event)
        self._used_pressure = self._manual_path[0]['p'] is not None
    
    """
    def on_stylus_down(self, gesture, x, y):
        #self.set_common_values(event.button, event_x, event_y)
        print("Stylus down.")
        self._manual_path = []
        print(f"Stylus down: x={x}, y={y}")
        success,pressure = gesture.get_axis(Gdk.AxisUse.PRESSURE)
        if success:
            print(f"  pressure: {pressure:.2f}")
        success,x_value = gesture.get_axis(Gdk.AxisUse.X)
        if success:
            print(f"  x: {x_value}")
        success,y_value = gesture.get_axis(Gdk.AxisUse.Y)
        if success:
            print(f"  y: {y_value}")
        new_point = {
            'x': x_value,
            'y': y_value,
            'p': pressure
        }
        self._manual_path.append(new_point)
        self._used_pressure = self._manual_path[0]['p'] is not None

    """

    def on_motion_on_area(self, event, surface, event_x, event_y, render=True):
        self._add_pressured_point(event_x, event_y, event)
        if render:
            operation = self.build_operation()
            self.do_tool_operation(operation)

    """
    def on_stylus_motion(self, gesture, sequence):
        success,pressure = gesture.get_axis(Gdk.AxisUse.PRESSURE)
        if success:
            print(f"  pressure: {pressure:.2f}")
        success,x_value = gesture.get_axis(Gdk.AxisUse.X)
        if success:
            print(f"  x: {x_value}")
        success,y_value = gesture.get_axis(Gdk.AxisUse.Y)
        if success:
            print(f"  y: {y_value}")
        new_point = {
            'x': x_value,
            'y': y_value,
            'p': pressure
        }
        self._manual_path.append(new_point)
        operation = self.build_operation()
        self.do_tool_operation(operation)

    def on_stylus_proximity(self, gesture, sequence):
        pass
    """

    def on_release_on_area(self, event, surface, event_x, event_y):
        self._add_pressured_point(event_x, event_y, event)
        operation = self.build_operation()
        operation['is_preview'] = False
        self.apply_operation(operation)

    """
    def on_stylus_up(self, gesture, sequence):
        success,pressure = gesture.get_axis(Gdk.AxisUse.PRESSURE)
        if success:
            print(f"  pressure: {pressure:.2f}")
        success,x_value = gesture.get_axis(Gdk.AxisUse.X)
        if success:
            print(f"  x: {x_value}")
        success,y_value = gesture.get_axis(Gdk.AxisUse.Y)
        if success:
            print(f"  y: {y_value}")
        new_point = {
            'x': x_value,
            'y': y_value,
            'p': pressure
        }
        self._manual_path.append(new_point)
        operation = self.build_operation()
        operation['is_preview'] = False
        self.apply_operation(operation)
    """

    ############################################################################

    def _add_pressured_point(self, event_x, event_y, event):
        new_point = {
            'x': event_x,
            'y': event_y,
            'p': self._get_pressure(event)
        }
        self._manual_path.append(new_point)

    def _get_pressure(self, event):
        device = event.get_source_device()
        if device is None:
            print("Device is None.")
            return None

        print(device.get_name())
        #print(device.get_vendor_id())
        #print(device.get_product_id())
        #print(device.get_n_axes())

        # source = device.get_source()
        # print(source) # J'ignore s'il faut faire quelque chose de cette info
        """
        axis_flags = device.get_axes()
        if (Gdk.AxisFlags.X & axis_flags) == Gdk.AxisFlags.X:
            print("Has X-axis")
        else:
            print("No X-axis")
        if (Gdk.AxisFlags.Y & axis_flags) == Gdk.AxisFlags.Y:
            print("Has Y-axis")
        else:
            print("No Y-axis")
        if (Gdk.AxisFlags.PRESSURE & axis_flags) == Gdk.AxisFlags.PRESSURE:
            print("Has Pressure info")
        else:
            print("No Pressure info")
        if (Gdk.AxisFlags.WHEEL & axis_flags) == Gdk.AxisFlags.WHEEL:
            print("Has Wheel info")
        else:
            print("No Wheel info")
        """

        tool = event.get_device_tool()
        # print(tool) # ça indique qu'on a ici un appareil dédié au dessin (vaut
        # `None` si c'est pas le cas). Autrement on peut avoir des valeurs comme
        # Gdk.DeviceToolType.PEN, .ERASER, .BRUSH, .PENCIL, ou .AIRBRUSH, et
        # aussi (même si jsuis pas sûr ce soit pertinent) .UNKNOWN, .MOUSE et
        # .LENS, on pourrait adapter le comportement (couleur/opérateur/etc.)
        # à cette information à l'avenir.

        #pressure = device.get_axis(axis_flags, Gdk.AxisUse.PRESSURE)
        # It reports device does not have get_axis method.
        # The original code uses Gdk.Event, which is a Union (not a class).
        # The return type for Gdk.Event.get_axis can be either NoneType or
        # float; and this is not a tuple.
        pressure = event.get_axis(Gdk.AxisUse.PRESSURE)
        print(f"Event.get_axis for pressure = {pressure}.")
        x_value = event.get_axis(Gdk.AxisUse.X)
        print(f"Event.get_axis for x = {x_value}.") 
        y_value = event.get_axis(Gdk.AxisUse.Y)
        print(f"Event.get_axis for y {y_value}.") 
        wheel = event.get_axis(Gdk.AxisUse.WHEEL)
        print(f"Event.get_axis for wheel {wheel}.") 
        if pressure is None:
            return None
        return pressure

    ############################################################################

    def build_operation(self):
        operation = {
            'tool_id': self.id,
            'brush_id': self._brush_type,
            'nib_dir': self._brush_dir,
            'rgba': self.main_color,
            'operator': self._operator,
            'line_width': self.tool_width,
            'antialias': self._use_antialias,
            'is_preview': True,
            'smooth': not self.get_image().is_zoomed_surface_sharp(),
            'path': self._manual_path
        }
        return operation

    def do_tool_operation(self, operation):
        if operation['path'] is None or len(operation['path']) < 1:
            return
        cairo_context = self.start_tool_operation(operation)

        active_brush = self._brushes_dict[operation['brush_id']]
        active_brush.do_brush_operation(cairo_context, operation)

    ############################################################################
################################################################################

