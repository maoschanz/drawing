project(
	'drawing',
	version: '0.5.4',
	meson_version: '>= 0.50.0',
)

# GTK and python-gi
dependency('gtk+-3.0', version : '>=3.22') # 3.24.22
dependency('pygobject-3.0', version : '>=3.30') # 3.36.1

# Equivalent of debian's python3-gi-cairo
dependency('py3cairo') # 1.18.0, debian's python-cairo?
# dependency('cairo-gobject') # 1.16.0 debian's libcairo-gobject2?

# Will be used in po and data
i18n = import('i18n')

subdir('data')
subdir('help')
subdir('src')
subdir('po')

meson.add_install_script('build-aux/meson/postinstall.py')

