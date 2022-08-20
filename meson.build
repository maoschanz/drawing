
project(
	'drawing',
	version: '1.2.0-dev',
	meson_version: '>= 0.50',
)
app_uuid = 'com.github.maoschanz.drawing'

# Dependencies #################################################################

# TODO the proper way to check python3 libs dependencies is this:
# https://mesonbuild.com/Python-module.html#dependency but the doc is quite bad
# so i've no idea how to make it work

################################################################################

# Will be used in po and data
if get_option('enable-translations-and-appdata')
	i18n = import('i18n')
endif

# Will be used in help and src
gnome = import('gnome')

subdir('data')
subdir('src')
subdir('po')
subdir('help')

meson.add_install_script('build-aux/meson/postinstall.py')

################################################################################

