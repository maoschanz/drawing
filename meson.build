project(
	'drawing',
	version: '0.4.15',
	meson_version: '>= 0.45.0',
)
app_uuid = 'com.github.maoschanz.drawing'

################################################################################

# Will be used in po and data
i18n = import('i18n')

# Will be used in help and src
gnome = import('gnome')

subdir('data')
subdir('help')
subdir('src')
subdir('po')

meson.add_install_script('build-aux/meson/postinstall.py')

################################################################################

