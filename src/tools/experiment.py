# pencil.py

from gi.repository import Gtk, Gdk, Gio, GLib
import cairo

from .tools import ToolTemplate

class ToolExperiment(ToolTemplate):
	__gtype_name__ = 'ToolExperiment'

	use_size = True

	def __init__(self, window, **kwargs):
		super().__init__('experiment', _("Experiment"), 'applications-science-symbolic', window)
		self.past_x = -1.0
		self.past_y = -1.0
		self._path = None
		self.main_color = None

		self.selected_operator_label = "OVER"
		self.selected_operator = cairo.Operator.OVER

		self.add_tool_action_enum('experiment_operator', 'OVER', self.on_change_active_operator)

	def on_change_active_operator(self, *args):
		state_as_string = args[1].get_string()
		if state_as_string == args[0].get_state().get_string():
			return
		args[0].set_state(GLib.Variant.new_string(state_as_string))
		if state_as_string == 'CLEAR':
			self.selected_operator = cairo.Operator.CLEAR
			self.selected_operator_label = "CLEAR"
		elif state_as_string == 'SOURCE':
			self.selected_operator = cairo.Operator.SOURCE
			self.selected_operator_label = "SOURCE"
		elif state_as_string == 'OVER':
			self.selected_operator = cairo.Operator.OVER
			self.selected_operator_label = "OVER"
		elif state_as_string == 'IN':
			self.selected_operator = cairo.Operator.IN
			self.selected_operator_label = "IN"
		elif state_as_string == 'OUT':
			self.selected_operator = cairo.Operator.OUT
			self.selected_operator_label = "OUT"
		elif state_as_string == 'ATOP':
			self.selected_operator = cairo.Operator.ATOP
			self.selected_operator_label = "ATOP"
		elif state_as_string == 'DEST':
			self.selected_operator = cairo.Operator.DEST
			self.selected_operator_label = "DEST"
		elif state_as_string == 'DEST_OVER':
			self.selected_operator = cairo.Operator.DEST_OVER
			self.selected_operator_label = "DEST_OVER"
		elif state_as_string == 'DEST_IN':
			self.selected_operator = cairo.Operator.DEST_IN
			self.selected_operator_label = "DEST_IN"
		elif state_as_string == 'DEST_OUT':
			self.selected_operator = cairo.Operator.DEST_OUT
			self.selected_operator_label = "DEST_OUT"
		elif state_as_string == 'DEST_ATOP':
			self.selected_operator = cairo.Operator.DEST_ATOP
			self.selected_operator_label = "DEST_ATOP"
		elif state_as_string == 'XOR':
			self.selected_operator = cairo.Operator.XOR
			self.selected_operator_label = "XOR"
		elif state_as_string == 'ADD':
			self.selected_operator = cairo.Operator.ADD
			self.selected_operator_label = "ADD"
		elif state_as_string == 'SATURATE':
			self.selected_operator = cairo.Operator.SATURATE
			self.selected_operator_label = "SATURATE"
		elif state_as_string == 'MULTIPLY':
			self.selected_operator = cairo.Operator.MULTIPLY
			self.selected_operator_label = "MULTIPLY"
		elif state_as_string == 'SCREEN':
			self.selected_operator = cairo.Operator.SCREEN
			self.selected_operator_label = "SCREEN"
		elif state_as_string == 'OVERLAY':
			self.selected_operator = cairo.Operator.OVERLAY
			self.selected_operator_label = "OVERLAY"
		elif state_as_string == 'DARKEN':
			self.selected_operator = cairo.Operator.DARKEN
			self.selected_operator_label = "DARKEN"
		elif state_as_string == 'LIGHTEN':
			self.selected_operator = cairo.Operator.LIGHTEN
			self.selected_operator_label = "LIGHTEN"
		elif state_as_string == 'COLOR_DODGE':
			self.selected_operator = cairo.Operator.COLOR_DODGE
			self.selected_operator_label = "COLOR_DODGE"
		elif state_as_string == 'COLOR_BURN':
			self.selected_operator = cairo.Operator.COLOR_BURN
			self.selected_operator_label = "COLOR_BURN"
		elif state_as_string == 'HARD_LIGHT':
			self.selected_operator = cairo.Operator.HARD_LIGHT
			self.selected_operator_label = "HARD_LIGHT"
		elif state_as_string == 'SOFT_LIGHT':
			self.selected_operator = cairo.Operator.SOFT_LIGHT
			self.selected_operator_label = "SOFT_LIGHT"
		elif state_as_string == 'DIFFERENCE':
			self.selected_operator = cairo.Operator.DIFFERENCE
			self.selected_operator_label = "DIFFERENCE"
		elif state_as_string == 'EXCLUSION':
			self.selected_operator = cairo.Operator.EXCLUSION
			self.selected_operator_label = "EXCLUSION"
		elif state_as_string == 'HSL_HUE':
			self.selected_operator = cairo.Operator.HSL_HUE
			self.selected_operator_label = "HSL_HUE"
		elif state_as_string == 'HSL_SATURATION':
			self.selected_operator = cairo.Operator.HSL_SATURATION
			self.selected_operator_label = "HSL_SATURATION"
		elif state_as_string == 'HSL_COLOR':
			self.selected_operator = cairo.Operator.HSL_COLOR
			self.selected_operator_label = "HSL_COLOR"
		elif state_as_string == 'HSL_LUMINOSITY':
			self.selected_operator = cairo.Operator.HSL_LUMINOSITY
			self.selected_operator_label = "HSL_LUMINOSITY"

	def get_options_model(self):
		builder = Gtk.Builder.new_from_resource("/com/github/maoschanz/Drawing/tools/ui/experiment.ui")
		return builder.get_object('options-menu')

	def get_options_label(self):
		return self.selected_operator_label

	def on_motion_on_area(self, area, event, surface):
		self.restore_pixbuf()
		w_context = cairo.Context(self.window.get_surface())
		w_context.set_operator(self.selected_operator)
		w_context.set_line_cap(cairo.LineCap.ROUND)
		w_context.set_line_join(cairo.LineJoin.ROUND)
		w_context.set_line_width(self.tool_width)
		w_context.set_source_rgba(self.main_color.red, self.main_color.green, \
				self.main_color.blue, self.main_color.alpha)
		if self.past_x == -1.0:
			(self.past_x, self.past_y) = (self.x_press, self.y_press)
			w_context.move_to(self.x_press, self.y_press)
			self._path = w_context.copy_path()
		else:
			w_context.append_path(self._path)
		w_context.line_to(event.x, event.y)
		w_context.stroke_preserve() # draw the line without closing the path
		self._path = w_context.copy_path()
		self.non_destructive_show_modif()
		self.past_x = event.x
		self.past_y = event.y

	def on_press_on_area(self, area, event, surface, tool_width, left_color, right_color):
		self.x_press = event.x
		self.y_press = event.y
		self.tool_width = tool_width
		if event.button == 3:
			self.main_color = right_color
		else:
			self.main_color = left_color

	def on_release_on_area(self, area, event, surface):
		self.past_x = -1.0
		self.past_y = -1.0
		self.apply_to_pixbuf()

