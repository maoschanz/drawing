
project(
	'drawing',
	version: '0.6.5',
	meson_version: '>= 0.50.0',
)
app_uuid = 'com.github.maoschanz.drawing'

# Dependencies #################################################################

# XXX the proper way to check python3 libs dependencies is this:
# https://mesonbuild.com/Python-module.html#dependency but the doc is quite bad
# so i've no idea how to make it work

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

