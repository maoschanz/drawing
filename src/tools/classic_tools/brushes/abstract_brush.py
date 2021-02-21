# Licensed under GPL3 https://github.com/maoschanz/drawing/blob/master/LICENSE

import cairo

class AbstractBrush():
	__gtype_name__ = 'AbstractBrush'

	def __init__(self, brush_id, brush_tool, *args):
		self._id = brush_id
		self._tool = brush_tool

	############################################################################

	def draw_preview(self, operation, cairo_context):
		cairo_context.set_operator(operation['operator'])
		cairo_context.set_line_width(operation['line_width'])
		cairo_context.new_path()
		for pt in operation['path']:
			cairo_context.line_to(pt['x'], pt['y'])
		cairo_context.stroke()

	def operation_on_mask(self, operation, original_context):
		if operation['operator'] == cairo.Operator.CLEAR \
		or operation['operator'] == cairo.Operator.SOURCE:
			# When using CLEAR or SOURCE, we don't need to use a temporary
			# surface, and actually we can't because using it as a mask would
			# just erase the entire image.
			original_context.set_operator(operation['operator'])
			c = operation['rgba']
			original_context.set_source_rgba(c.red, c.green, c.blue, c.alpha)
			self.do_masked_brush_op(original_context, operation)
			return

		# Creation of a blank surface with a new context; each brush decides how
		# to apply the options set by the user (`operation`), except for the
		# operator which has to be "wrongly" set to SOURCE.
		w = self._tool.get_surface().get_width()
		h = self._tool.get_surface().get_height()
		mask = cairo.ImageSurface(cairo.Format.ARGB32, w, h)
		context2 = cairo.Context(mask)
		context2.set_operator(cairo.Operator.SOURCE)
		rgba = operation['rgba']
		context2.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)

		self.do_masked_brush_op(context2, operation)

		# Paint the surface onto the actual image with the chosen operator
		original_context.set_operator(operation['operator'])
		original_context.set_source_surface(mask)
		original_context.paint()

	############################################################################

	def do_brush_operation(self, cairo_context, operation):
		pass

	def do_masked_brush_op(self, cairo_context, operation):
		pass

	############################################################################
################################################################################

