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
  'preferences.py',
  'window.py',
  'pixbuf_manager.py',
  'tools.py',

  'crop_dialog.py',
  'scale_dialog.py',
  'rotate_dialog.py',
  'properties.py',

  'tools/experiment.py',
  'tools/line.py',
  'tools/paint.py',
  'tools/pencil.py',
  'tools/text.py',
  'tools/select.py',
  'tools/shape.py',
  'tools/polygon.py',
  'tools/picker.py',
  'tools/eraser.py'
]

install_data(drawing_sources, install_dir: moduledir)