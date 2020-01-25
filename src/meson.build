pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, meson.project_name())
gnome = import('gnome')

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

configure_file(
	input: meson.project_name() + '.in',
	output: meson.project_name(),
	configuration: conf,
	install: true,
	install_dir: get_option('bindir')
)

drawing_sources = [
	'__init__.py',
	'main.py',

	'window.py',
	'options_manager.py',
	'headerbar.py',
	'bottombar.py',
	'minimap.py',
	'color_popover.py',

	'image.py',
	'selection_manager.py',

	'utilities.py',
	'properties.py',
	'preferences.py',
	'message_dialog.py',
	'custom_image.py',

	'tools/abstract_tool.py',
	'tools/utilities_tools.py',

	'tools/classic_tools/abstract_classic_tool.py',
	'tools/classic_tools/classic_panel.py',
	'tools/classic_tools/tool_arc.py',
	'tools/classic_tools/tool_eraser.py',
	'tools/classic_tools/tool_experiment.py',
	'tools/classic_tools/tool_highlight.py',
	'tools/classic_tools/tool_line.py',
	'tools/classic_tools/tool_paint.py',
	'tools/classic_tools/tool_pencil.py',
	'tools/classic_tools/tool_picker.py',
	'tools/classic_tools/tool_shape.py',
	'tools/classic_tools/tool_text.py',

	'tools/selection_tools/abstract_select.py',
	'tools/selection_tools/selection_panel.py',
	'tools/selection_tools/rect_select.py',
	'tools/selection_tools/free_select.py',
	'tools/selection_tools/color_select.py',

	'tools/canvas_tools/abstract_canvas_tool.py',
	'tools/canvas_tools/tool_crop.py',
	'tools/canvas_tools/tool_filters.py',
	'tools/canvas_tools/tool_matrix.py',
	'tools/canvas_tools/tool_rotate.py',
	'tools/canvas_tools/tool_scale.py'
]

install_data(drawing_sources, install_dir: moduledir)
