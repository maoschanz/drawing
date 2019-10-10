project(
	'drawing',
	version: '0.4.7',
	meson_version: '>= 0.45.0',
)

i18n = import('i18n')

subdir('data')
subdir('help')
subdir('src')
subdir('po')

meson.add_install_script('build-aux/meson/postinstall.py')
