
project(
	'drawing',
	version: '1.2.0-dev',
	meson_version: '>= 0.50',
)
app_uuid = 'com.github.maoschanz.drawing'

# Dependencies 
pygobject = dependency('pygobject-3.0', version: '>=3.0.0')

py_module = import('python')
py_instln = py_module.find_installation('python3')
py_dep    = py_instln.dependency()


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
