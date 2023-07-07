
pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, meson.project_name())

gnome.compile_resources(meson.project_name(),
	meson.project_name() + '.gresource.xml',
	gresource_bundle: true,
	install: true,
	install_dir: pkgdatadir,
)

python3 = import('python3')

conf = configuration_data()
conf.set('PYTHON', python3.find_python().path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

if get_option('use-uuid-as-binary-name')
	binary_name = app_uuid
else
	binary_name = meson.project_name()
endif

configure_file(
	input: meson.project_name() + '.in',
	output: binary_name,
	configuration: conf,
	install: true,
	install_dir: get_option('bindir')
)

drawing_sources = [
	'__init__.py',
	'main.py',

	'window.py',
	'deco_manager.py',
	'options_manager.py',
	'minimap.py',
	'tools_initializer.py',

	'image.py',
	'history_state.py',
	'history_manager.py',
	'printing_manager.py',
	'saving_manager.py',
	'selection_manager.py',

	'properties.py',
	'preferences.py',
	'message_dialog.py',
	'new_image_dialog.py',

	'utilities/utilities_blur.py',
	'utilities/utilities_colors.py',
	'utilities/utilities_files.py',
	'utilities/utilities_overlay.py',
	'utilities/utilities_paths.py',
	'utilities/utilities_units.py',

	'optionsbars/abstract_optionsbar.py',
	'optionsbars/classic/optionsbar_classic.py',
	'optionsbars/classic/optionsbar_color_popover.py',
	'optionsbars/selection/optionsbar_selection.py',
	'optionsbars/transform/optionsbar_crop.py',
	'optionsbars/transform/optionsbar_filters.py',
	'optionsbars/transform/optionsbar_rotate.py',
	'optionsbars/transform/optionsbar_scale.py',
	'optionsbars/transform/optionsbar_skew.py',

	'tools/abstract_tool.py',

	'tools/classic_tools/abstract_classic_tool.py',
	'tools/classic_tools/tool_arc.py',
	'tools/classic_tools/tool_brush.py',
	'tools/classic_tools/tool_eraser.py',
	'tools/classic_tools/tool_experiment.py',
	'tools/classic_tools/tool_highlight.py',
	'tools/classic_tools/tool_line.py',
	'tools/classic_tools/tool_paint.py',
	'tools/classic_tools/tool_pencil.py',
	'tools/classic_tools/tool_picker.py',
	'tools/classic_tools/tool_points.py',
	'tools/classic_tools/tool_shape.py',
	'tools/classic_tools/tool_text.py',

	'tools/classic_tools/brushes/abstract_brush.py',
	'tools/classic_tools/brushes/brush_airbrush.py',
	'tools/classic_tools/brushes/brush_nib.py',
	'tools/classic_tools/brushes/brush_hairy.py',
	'tools/classic_tools/brushes/brush_simple.py',

	'tools/classic_tools/erasers/abstract_eraser.py',
	'tools/classic_tools/erasers/eraser_area.py',
	'tools/classic_tools/erasers/eraser_color.py',
	'tools/classic_tools/erasers/eraser_rubber.py',

	'tools/selection_tools/abstract_select.py',
	'tools/selection_tools/select_rect.py',
	'tools/selection_tools/select_free.py',
	'tools/selection_tools/select_color.py',

	'tools/transform_tools/abstract_transform_tool.py',
	'tools/transform_tools/tool_crop.py',
	'tools/transform_tools/tool_filters.py',
	'tools/transform_tools/tool_rotate.py',
	'tools/transform_tools/tool_scale.py',
	'tools/transform_tools/tool_skew.py',

	'tools/transform_tools/filters/abstract_filter.py',
	'tools/transform_tools/filters/filter_blur.py',
	'tools/transform_tools/filters/filter_colors.py',
	'tools/transform_tools/filters/filter_contrast.py',
	'tools/transform_tools/filters/filter_emboss.py',
	'tools/transform_tools/filters/filter_saturation.py',
	'tools/transform_tools/filters/filter_transparency.py',
	'tools/transform_tools/filters/filter_veil.py',
]

install_data(drawing_sources, install_dir: moduledir)

