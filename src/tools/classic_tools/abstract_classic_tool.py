# abstract_select.py

import cairo
from gi.repository import Gtk

from .abstract_tool import AbstractAbstractTool
from .bottombar import DrawingAdaptativeBottomBar
from .color_popover import DrawingColorPopover

from .utilities import utilities_add_unit_to_spinbtn
from .utilities_tools import utilities_fast_blur

class AbstractClassicTool(AbstractAbstractTool):
	__gtype_name__ = 'AbstractClassicTool'

	def __init__(self, tool_id, label, icon_name, window, **kwargs):
		super().__init__(tool_id, label, icon_name, window)
		self.menu_id = 0
		self.use_color = True
		self.use_size = True
		self.accept_selection = False
		self.tool_width = 1
		self.main_color = None
		self.secondary_color = None

	############################################################################
	# UI implementations #######################################################

	def try_build_panel(self):
		self.panel_id = 'classic'
		self.window.options_manager.try_add_bottom_panel(self.panel_id, self)

	def build_bottom_panel(self):
		return ClassicToolPanel(self.window)

	def on_tool_selected(self):
		# TODO update the label/menu/size/sensitivity/etc.
		pass

	############################################################################
	# ................................ #########################################

	def set_common_values(self, event_btn):
		self.tool_width = self.window.options_manager.get_tool_width()
		if event_btn == 1:
			self.main_color = self.window.options_manager.get_left_color()
			self.secondary_color = self.window.options_manager.get_right_color()
		if event_btn == 3:
			self.main_color = self.window.options_manager.get_right_color()
			self.secondary_color = self.window.options_manager.get_left_color()

	def get_operator_enum(self):
		return self.window.options_manager.get_operator()[0]

	############################################################################
	# Operations management ####################################################

	# def build_operation(self):
	# 	pass

	# def do_tool_operation(self, operation):
	# 	super().do_tool_operation(operation)

	def stroke_with_operator(self, operator, cairo_context, line_width, is_preview):
		cairo_context.set_operator(operator)
		is_blur = (operator == cairo.Operator.DEST_IN)
		if is_blur and is_preview:
			cairo_context.set_operator(cairo.Operator.CLEAR)

		if is_blur and not is_preview:
			cairo_context.set_line_width(2*line_width)
			cairo_context.stroke()
			radius = int(line_width/2)
			# TODO only give the adequate rectangle, not the whole image, it's too slow!
			b_surface = utilities_fast_blur(self.get_surface(), radius, 0)
			# where 0 == BlurType.AUTO
			self.restore_pixbuf()
			cairo_context = self.get_context()
			cairo_context.set_operator(cairo.Operator.OVER)
			cairo_context.set_source_surface(b_surface, 0, 0)
			cairo_context.paint()
		else:
			cairo_context.set_line_width(line_width)
			cairo_context.stroke()

	############################################################################
################################################################################

class ClassicToolPanel(DrawingAdaptativeBottomBar):
	__gtype_name__ = 'ClassicToolPanel'

	def __init__(self, window):
		super().__init__()
		self.window = window
		builder = self.build_ui('ui/classic-panel.ui')

		self.color_box = builder.get_object('color_box')
		self.color_menu_btn_r = builder.get_object('color_menu_btn_r')
		self.color_menu_btn_l = builder.get_object('color_menu_btn_l')
		self.build_color_buttons(builder)

		self.options_btn = builder.get_object('options_btn')
		self.options_label = builder.get_object('options_label')
		self.options_long_box = builder.get_object('options_long_box')
		self.options_short_box = builder.get_object('options_short_box')

		self.thickness_scalebtn = builder.get_object('thickness_scalebtn')
		self.thickness_spinbtn = builder.get_object('thickness_spinbtn')
		self.thickness_spinbtn.set_value(self.window._settings.get_int('last-size'))
		utilities_add_unit_to_spinbtn(self.thickness_spinbtn, 3, 'px') # XXX fonctionne mais c'est moche mdr

		self.minimap_btn = builder.get_object('minimap_btn')
		self.minimap_label = builder.get_object('minimap_label')
		self.minimap_arrow = builder.get_object('minimap_arrow')

	def update_for_new_tool(self, tool):
		self.color_box.set_sensitive(tool.use_color)
		self.thickness_scalebtn.set_sensitive(tool.use_size)
		self.thickness_spinbtn.set_sensitive(tool.use_size)

	def get_minimap_btn(self):
		return self.minimap_btn

	def set_minimap_label(self, label):
		self.minimap_label.set_label(label)

	def toggle_options_menu(self):
		self.options_btn.set_active(not self.options_btn.get_active())

	def hide_options_menu(self):
		self.options_btn.set_active(False)
		self.color_popover_r.update_mode()
		self.color_popover_l.update_mode()

	def set_operator(self, op_as_string):
		if op_as_string == 'difference':
			self.selected_operator_enum = cairo.Operator.DIFFERENCE
			self.selected_operator_label = _("Difference")
		elif op_as_string == 'source':
			self.selected_operator_enum = cairo.Operator.SOURCE
			self.selected_operator_label = _("Source color")
		elif op_as_string == 'clear':
			self.selected_operator_enum = cairo.Operator.CLEAR
			self.selected_operator_label = _("Eraser")
		elif op_as_string == 'dest_in':
			self.selected_operator_enum = cairo.Operator.DEST_IN
			self.selected_operator_label = _("Blur")
		else:
			self.selected_operator_enum = cairo.Operator.OVER
			self.selected_operator_label = _("Classic")

	def build_color_buttons(self, builder):
		"""Initialize the 2 color buttons and popovers with the 2 previously
		memorized RGBA values."""
		right_rgba = self.window._settings.get_strv('last-right-rgba')
		left_rgba = self.window._settings.get_strv('last-left-rgba')
		self.color_popover_r = DrawingColorPopover(self.color_menu_btn_r, \
		      builder.get_object('r_btn_image'), right_rgba, False, self.window)
		self.color_popover_l = DrawingColorPopover(self.color_menu_btn_l, \
		        builder.get_object('l_btn_image'), left_rgba, True, self.window)

	def set_palette_setting(self, show_editor):
		self.color_popover_r.setting_changed(show_editor)
		self.color_popover_l.setting_changed(show_editor)

	def build_options_menu(self, widget, model, label):
		if widget is not None:
			self.options_btn.set_popover(widget)
		elif model is not None:
			self.options_btn.set_menu_model(model)
		else:
			self.options_btn.set_popover(None)
		self.options_label.set_label(label)

	def init_adaptability(self):
		super().init_adaptability()
		temp_limit_size = self.color_box.get_preferred_width()[0] + \
		          self.thickness_spinbtn.get_preferred_width()[0] + \
		           self.options_long_box.get_preferred_width()[0] + \
		                self.minimap_btn.get_preferred_width()[0]
		self.set_limit_size(temp_limit_size)

	def set_compact(self, state):
		super().set_compact(state)
		self.options_long_box.set_visible(not state)
		self.options_short_box.set_visible(state)
		self.thickness_scalebtn.set_visible(state)
		self.thickness_spinbtn.set_visible(not state)
		self.minimap_arrow.set_visible(not state)

	############################################################################
################################################################################

