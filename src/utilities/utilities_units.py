# Licensed under GPL3 https://github.com/maoschanz/drawing/blob/master/LICENSE

from gi.repository import Gtk

################################################################################

def utilities_add_unit_to_spinbtn(spinbutton, width_chars, unit):
	spinbutton.set_width_chars(width_chars + 3)
	if unit == 'px':
		# To translators: it's a measure unit, it appears in tooltips over
		# numerical inputs
		_add_spinbutton_icon(spinbutton, 'unit-pixels-symbolic', _("pixels"))
	elif unit == '%':
		# To translators: it appears in tooltips over numerical inputs
		_add_spinbutton_icon(spinbutton, 'unit-percents-symbolic', _("percents"))
	elif unit == '°':
		# To translators: it's the angle measure unit, it appears in a tooltip
		# over a numerical input
		_add_spinbutton_icon(spinbutton, 'unit-degrees-symbolic', _("degrees"))

def _add_spinbutton_icon(spinbutton, icon, tooltip):
	p = Gtk.EntryIconPosition.SECONDARY
	spinbutton.set_icon_from_icon_name(p, icon)
	spinbutton.set_icon_tooltip_text(p, tooltip)
	spinbutton.set_icon_sensitive(p, False)

################################################################################

