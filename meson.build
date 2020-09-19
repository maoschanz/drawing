
project(
	'drawing',
	version: '0.6.0',
	meson_version: '>= 0.50.0',
)
app_uuid = 'com.github.maoschanz.drawing'

# Dependencies #################################################################

# dependency('gtk+-3.0', version: '>=3.22')
# dependency('pygobject-3.0', version: '>=3.30') # python3-gi, python3-gi-cairo
# dependency('py3cairo') # python3, cairo, python3-cairo
# XXX ^ this puts dependencies on *-dev packages during the build process, but
# it doesn't ensure the actual lib is here

python3 = find_program('python3')
# You can comment the following instruction if you're using an old distro to
# build a package for a recent distro. These modules are required to run the
# app, but not to build the package
python3_tested_modules = {
	'cairo': '',
	'gi': '3.30',
}

foreach module, required_version : python3_tested_modules
	if run_command(python3, '-c', 'import @0@'.format(module)).returncode() != 0
		error('python3 module \'' + module + '\' not found')
	else
		test_module = run_command(
			python3,
			'-c',
			'import @0@, sys; print (sys.modules["@0@"].__version__)'.format(module)
		)
		actual_version = test_module.stdout().strip()
	endif
	if required_version > actual_version
		error(
			'python3 module "' + module + '" found with version "' + actual_version
			+ '", the version "' + required_version + '" is required.'
		)
	else
		message('python3 module "' + module + '" looks fine.')
	endif
endforeach

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

