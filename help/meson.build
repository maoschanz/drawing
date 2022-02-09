
if get_option('enable-translations-and-appdata') and meson.version().version_compare('>= 0.61')
	itstool = find_program('itstool')
else
	itstool = false
endif

if not itstool
	i18n = []
endif

gnome.yelp(
	meson.project_name(),
	sources: [
		'fullscreen.page',
		'index.page',
		'legal.xml',
		'main_features.page',
		'preferences.page',
		'tools_classic.page',
		'tools_classic_colors.page',
		'tools_selection.page',
		'tools_transform.page',
		'whats_new.page',
		'zoom_preview.page'
	],
	media: [
		'figures/icon.png',
		'figures/screenshot_arrow.png', # 0.8.0
		'figures/screenshot_color_editor.png', # 0.8.0
		'figures/screenshot_color_palette.png', # 0.8.0
		'figures/screenshot_filters.png', # 0.6.?
		'figures/screenshot_fullscreen.png', # 0.8.0
		'figures/screenshot_hsl.png', # 0.8.0
		'figures/screenshot_menu.png', # 0.8.0
		'figures/screenshot_prefs_images.png', # 0.8.0
		'figures/screenshot_prefs_tools.png', # 0.8.0
		'figures/screenshot_scale.png', # 0.8.0
		'figures/screenshot_selection.png', # 0.8.0
		'figures/screenshot_text.png', # 0.8.0
		'figures/screenshot_zoom.png' # 0.8.0
	]
)

