# abstract_select.py

from gi.repository import Gtk
import cairo

from .abstract_tool import ToolTemplate
from .bottombar import DrawingAdaptativeBottomBar
from .color_popover import DrawingColorPopover
from .utilities import utilities_add_px_to_spinbutton

class AbstractClassicTool(ToolTemplate):
	__gtype_name__ = 'AbstractClassicTool'

	def __init__(self, tool_id, label, icon_name, window, **kwargs):
		super().__init__(tool_id, label, icon_name, window)
		self.menu_id = 0
		self.use_color = True # TODO inutile maintenant ?
		self.accept_selection = False
		self.tool_width = 1
		self.main_color = None
		self.secondary_color = None

	############################################################################
	# UI implementations #######################################################

	def adapt_to_window_size(self, available_width):
		return
		self.needed_width_for_long = 400
		# TODO refaire proprement avec une implémentation de bottombar
		if self.needed_width_for_long > 0.8 * available_width:
			self.compact_bottombar(True)
		else:
			self.compact_bottombar(False)

	def compact_bottombar(self, state):
		self.options_long_box.set_visible(not state)
		self.minimap_label.set_visible(not state)
		self.minimap_arrow.set_visible(not state)
		self.options_short_box.set_visible(state)
		self.minimap_icon.set_visible(state)

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

	def set_common_values(self, event):
		self.tool_width = self.window.options_manager.get_tool_width()
		if event.button == 1:
			self.main_color = self.window.options_manager.get_left_color()
			self.secondary_color = self.window.options_manager.get_right_color()
		if event.button == 3:
			self.main_color = self.window.options_manager.get_right_color()
			self.secondary_color = self.window.options_manager.get_left_color()

	############################################################################
	# Path management ##########################################################

	# TODO pour l'instant c'est dans utilities, ça doit ptêt y rester

	############################################################################
	# Operations management ####################################################

	def build_operation(self):
		pass

	def do_tool_operation(self, operation):
		pass

	############################################################################
################################################################################

class ClassicToolPanel(DrawingAdaptativeBottomBar):
	__gtype_name__ = 'ClassicToolPanel'

	def __init__(self, window):
		super().__init__()
		self.window = window
		builder = self.build_ui('ui/panel_classic.ui')
		# ... TODO
		#
		# bar.widgets_narrow = []
		# bar.widgets_wide = []
		#
		#

		self.color_box = builder.get_object('color_box')
		self.color_menu_btn_r = builder.get_object('color_menu_btn_r')
		self.color_menu_btn_l = builder.get_object('color_menu_btn_l')
		self.r_btn_image = builder.get_object('r_btn_image')
		self.l_btn_image = builder.get_object('l_btn_image')
		self.build_color_buttons()

		self.options_btn = builder.get_object('options_btn')
		self.options_label = builder.get_object('options_label')
		self.options_btn.show_all() # XXX

		self.thickness_scalebtn = builder.get_object('thickness_scalebtn')
		self.thickness_spinbtn = builder.get_object('thickness_spinbtn')
		self.thickness_spinbtn.set_value(self.window._settings.get_int('last-size'))
		utilities_add_px_to_spinbutton(self.thickness_spinbtn, 3, 'px') # XXX fonctionne mais c'est moche mdr

		self.minimap_btn = builder.get_object('minimap_btn')
		self.minimap_label = builder.get_object('minimap_label')
		# .....
		self.minimap_btn.show_all() # XXX

	def update_for_new_tool(self, tool): # and the menu? XXX
		self.color_box.set_sensitive(tool.use_color)
		self.thickness_scalebtn.set_sensitive(tool.use_size)
		self.thickness_spinbtn.set_sensitive(tool.use_size)

	def get_minimap_btn(self):
		return self.minimap_btn

	def set_minimap_label(self, label):
		self.minimap_label.set_label(label)

	def build_color_buttons(self):
		"""Initialize the 2 color buttons and popovers with the 2 previously
		memorized RGBA values."""
		right_rgba = self.window._settings.get_strv('last-right-rgba')
		left_rgba = self.window._settings.get_strv('last-left-rgba')
		self.color_popover_r = DrawingColorPopover(self.color_menu_btn_r, \
		                                           self.r_btn_image, right_rgba)
		self.color_popover_l = DrawingColorPopover(self.color_menu_btn_l, \
		                                           self.l_btn_image, left_rgba)

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



	############################################################################
################################################################################
