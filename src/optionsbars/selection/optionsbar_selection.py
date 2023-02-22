# Licensed under GPL3 https://github.com/maoschanz/drawing/blob/master/LICENSE

from .abstract_optionsbar import AbstractOptionsBar

class OptionsBarSelection(AbstractOptionsBar):
	__gtype_name__ = 'OptionsBarSelection'

	def __init__(self, window):
		super().__init__()
		self.window = window
		builder = self._build_ui('selection/optionsbar-selection.ui')

		self.import_box_narrow = builder.get_object('import_box_narrow')
		self.import_box_long = builder.get_object('import_box_long')
		self.clipboard_box = builder.get_object('clipboard_box')

		self.actions_btn = builder.get_object('actions_btn')
		self.actions_btn_long = builder.get_object('actions_btn_long')
		self._togglable_btn = self.actions_btn

		self.minimap_btn = builder.get_object('minimap_btn')
		self.minimap_label = builder.get_object('minimap_label')
		self.minimap_arrow = builder.get_object('minimap_arrow')

	def get_minimap_btn(self):
		return self.minimap_btn

	def set_minimap_label(self, label):
		self.minimap_label.set_label(label)

	def middle_click_action(self):
		self.window.lookup_action('new_tab_selection').activate()

	############################################################################

	def init_adaptability(self):
		super().init_adaptability()
		temp_limit_size = self.import_box_long.get_preferred_width()[0] + \
		                    self.clipboard_box.get_preferred_width()[0] + \
		                      self.actions_btn.get_preferred_width()[0] + \
		                      self.options_btn.get_preferred_width()[0] + \
		                         self.help_btn.get_preferred_width()[0] + \
		                      self.minimap_btn.get_preferred_width()[0]
		self._set_limit_size(temp_limit_size)

	def set_compact(self, state):
		super().set_compact(state)
		self.import_box_narrow.set_visible(state)
		self.import_box_long.set_visible(not state)
		self.actions_btn.set_visible(not state)
		self.clipboard_box.set_visible(not state)
		if state:
			self._togglable_btn = self.actions_btn_long
		else:
			self._togglable_btn = self.actions_btn
		self.minimap_arrow.set_visible(not state)

	############################################################################
################################################################################

