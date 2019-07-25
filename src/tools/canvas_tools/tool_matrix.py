# tool_matrix.py
#
# Copyright 2019 Romain F. T.
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

from gi.repository import Gtk, Gdk, GdkPixbuf
import cairo

from .abstract_canvas_tool import AbstractCanvasTool

class ToolMatrix(AbstractCanvasTool):
	__gtype_name__ = 'ToolMatrix'

	def __init__(self, window):
		super().__init__('matrix', _("Deformation"), 'tool-matrix-symbolic', window)
		# self.cursor_name = ''
		self.apply_to_selection = False

		builder = Gtk.Builder.new_from_resource( \
		                '/com/github/maoschanz/drawing/tools/ui/tool_matrix.ui')
		self.bottom_panel = builder.get_object('bottom-panel')

		# TODO
		# le but est de remplacer :
		# - rotate
		# - flip
		# - scale
		# et d'introduire des features telles que :
		# - l'inclinaison comme dans Microsoft Paint
		# - les widgets sur la surface

		self.window.bottom_panel_box.add(self.bottom_panel)

	# TODO
		# ...

	############################################################################
################################################################################

