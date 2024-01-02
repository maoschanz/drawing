
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
		rename: app_uuid + '.desktop',
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

	appstreamcli = find_program('appstreamcli', required: false)
	if appstreamcli.found()
		test(
			'Validate appstream file',
			appstreamcli,
			args: ['validate', '--no-net', '--explain', appstream_file],
			workdir: meson.current_build_dir()
		)
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

