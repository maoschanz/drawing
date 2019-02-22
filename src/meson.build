pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'drawing')
gnome = import('gnome')

gnome.compile_resources('drawing',
	'drawing.gresource.xml',
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
	input: 'drawing.in',
	output: 'drawing',
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
	'color_popover.py',
	'options_manager.py',
	'minimap.py',
	'utilities.py',
	'tools.py',

	'properties.py',
	'preferences.py',

	'tools/tool_arc.py',
	'tools/tool_crop.py',
	'tools/tool_experiment.py',
	'tools/tool_flip.py',
	'tools/tool_freeshape.py',
	'tools/tool_line.py',
	'tools/tool_paint.py',
	'tools/tool_pencil.py',
	'tools/tool_polygon.py',
	'tools/tool_picker.py',
	'tools/tool_rotate.py',
	'tools/tool_saturate.py',
	'tools/tool_scale.py',
	'tools/tool_select.py',
	'tools/tool_shape.py',
	'tools/tool_text.py'
]

install_data(drawing_sources, install_dir: moduledir)
