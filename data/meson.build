
################################################################################
# Installation and validation of the .desktop file #############################

desktop_files_dir = join_paths(get_option('datadir'), 'applications')
if get_option('enable-translations-and-appdata')
	desktop_file = i18n.merge_file(
		input: app_uuid + '.desktop.in',
		output: app_uuid + '.desktop',
		type: 'desktop',
		po_dir: '../po',
		install: true,
		install_dir: desktop_files_dir
	)
else
	install_data(
		app_uuid + '.desktop.in',
		install_rename: app_uuid + '.desktop',
		install_dir: desktop_files_dir
	)
	desktop_file = desktop_files_dir / app_uuid + '.desktop'
endif

desktop_utils = find_program('desktop-file-validate', required: false)
if desktop_utils.found()
	test('Validate desktop file', desktop_utils, args: [desktop_file])
endif

################################################################################
# Installation and validation of the appstream file ############################

if get_option('enable-translations-and-appdata')
	appstream_file = i18n.merge_file(
		input: app_uuid + '.appdata.xml.in',
		output: app_uuid + '.appdata.xml',
		po_dir: '../po',
		install: true,
		install_dir: join_paths(get_option('datadir'), 'metainfo')
	)

	appstream_util = find_program('appstream-util', required: false)
	if appstream_util.found()
		test(
			'Validate appstream file',
			appstream_util,
			args: ['validate', appstream_file]
		)
		# The app will never pass "validate-strict" because appstream-util wants
		# pictures with a 16:9 ratio, while i use pictures of the default window
		# size, which is approximating the objectively better golden ratio.
	endif
endif

################################################################################
# Installation and validation of the .gschema file #############################

install_data(
	app_uuid + '.gschema.xml',
	install_dir: join_paths(get_option('datadir'), 'glib-2.0/schemas')
)

compile_schemas = find_program('glib-compile-schemas', required: false)
if compile_schemas.found()
	test(
		'Validate schema file',
		compile_schemas,
		args: ['--strict', '--dry-run', meson.current_source_dir()]
	)
endif

################################################################################

subdir('icons')

