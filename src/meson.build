
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

configure_file(
	input: meson.project_name() + '.in',
	output: meson.project_name(),
	configuration: conf,
	install: true,
	install_dir: get_option('bindir')
)

drawing_sources = [
	'__init__.py',
	'gi_composites.py',

	'main.py',
	'window.py',
	'image.py',
	'message_dialog.py',
	'color_popover.py',
	'options_manager.py',
	'headerbar.py',
	'minimap.py',
	'selection_manager.py',
	'utilities.py',

	'custom_image.py',
	'properties.py',
	'preferences.py',

	'tools/abstract_tool.py',

	'tools/classic_tools/tool_arc.py',
	'tools/classic_tools/tool_circle.py',
	'tools/classic_tools/tool_freeshape.py',
	'tools/classic_tools/tool_line.py',
	'tools/classic_tools/tool_paint.py',
	'tools/classic_tools/tool_pencil.py',
	'tools/classic_tools/tool_polygon.py',
	'tools/classic_tools/tool_picker.py',
	'tools/classic_tools/tool_rectangle.py',
	'tools/classic_tools/tool_text.py',

	'tools/selection_tools/tool_select.py',

	'tools/canvas_tools/abstract_canvas_tool.py',

	'tools/canvas_tools/tool_crop.py',
	'tools/canvas_tools/tool_flip.py',
	'tools/canvas_tools/tool_rotate.py',
	'tools/canvas_tools/tool_saturate.py',
	'tools/canvas_tools/tool_scale.py'
]

install_data(drawing_sources, install_dir: moduledir)
