#!/bin/bash

function src_lang () {
	src_pot
	echo "Updating translation for: $1"
	msgmerge --update --previous ./po/$1.po ./po/drawing.pot
}

function src_all () {
	ninja -C _build drawing-update-po

	# while IFS= read -r line; do
	# 	if [ ${line::1} != "#" ]; then
	# 		src_lang $line
	# 	fi
	# done < po/LINGUAS
	# rm po/*.po~
}

function src_pot () {
	echo "Updating .pot file for src"
	ninja -C _build drawing-pot
	# xgettext --files-from=po/POTFILES --from-code=UTF-8 -c --add-location=file --output=po/drawing.pot
}

function help_all () {
	echo "Updating .po files for help"
	ninja -C _build help-drawing-update-po
}

function help_pot () {
	ninja -C _build help-drawing-pot
	echo "Updating .pot file for help"
}

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

