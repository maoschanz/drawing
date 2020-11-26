
project(
	'drawing',
	version: '0.7.0+',
	meson_version: '>= 0.50.0',
)
app_uuid = 'com.github.maoschanz.drawing'

# Dependencies #################################################################

# XXX the proper way to check python3 libs dependencies is this:
# https://mesonbuild.com/Python-module.html#dependency but the doc is quite bad
# so i've no idea how to make it work

python3 = find_program('python3')
python3_tested_modules = {
	'cairo': '',
	'gi': '3.30',
}

# You can comment the following loop if you're using an old distro to build a
# package for a recent distro. These modules are required to run the app, but
# not to build the package
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

# TODO options to build it without gettext. If gettext, validate the dep is here
# TODO options to build it without appdata. If appdata, validate the dep is here

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

