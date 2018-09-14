pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'draw')
gnome = import('gnome')

gnome.compile_resources('draw',
  'draw.gresource.xml',
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
  input: 'draw.in',
  output: 'draw',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

draw_sources = [
  '__init__.py',
  'gi_composites.py',
  'main.py',
  'window.py',
  'tools.py',
  'image.py',
  'preferences.py',
  'tools/crop.py',
  'tools/line.py',
  'tools/paint.py',
  'tools/pencil.py',
  'tools/text.py',
  'tools/select.py',
  'tools/shape.py',
  'tools/picker.py',
  'tools/eraser.py'
]

install_data(draw_sources, install_dir: moduledir)