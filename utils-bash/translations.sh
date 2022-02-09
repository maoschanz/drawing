#!/bin/bash

function src_lang () {
	src_pot
	echo "Updating translation (src) for: $1"
	msgmerge --update --previous ./po/$1.po ./po/drawing.pot
}

function src_all () {
	echo "Updating all .po files (src)"
	ninja -C _build drawing-update-po

	# while IFS= read -r line; do
	# 	if [ ${line::1} != "#" ]; then
	# 		src_lang $line
	# 	fi
	# done < po/LINGUAS
	# rm po/*.po~
}

function src_pot () {
	echo "Updating .pot file (src)"
	ninja -C _build drawing-pot
	# xgettext --files-from=po/POTFILES --from-code=UTF-8 -c --add-location=file --output=po/drawing.pot
}

################################################################################

function help_lang () {
	help_pot

	# TODO if the dir doesn't exist,
	if false; then
		echo "Creating .po file (help) for: $1"
		echo $1 >> help/LINGUAS
		sort help/LINGUAS -o help/LINGUAS
		mkdir help/$1
		touch help/$1/$1.po
	fi

	help_all
}

function help_all () {
	echo "Updating all .po files (help)"
	ninja -C _build help-drawing-update-po
}

function help_pot () {
	echo "Updating .pot file (help)"
	ninja -C _build help-drawing-pot
}

################################################################################

if [ $# = 0 ]; then
	echo "Available methods:"
	declare -F
	echo ""
	echo "Running src_all by default"
	src_all
else
	$1 $2
fi

exit 0

