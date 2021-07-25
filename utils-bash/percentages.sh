#!/bin/bash

function absolute_values () {
	echo "| language | translated | approximative | untranslated |"
	echo "|----------|------------|---------------|--------------|"

	old_ifs=$IFS
	IFS=','

	cd po
	for i in *.po; do
		[ -f "$i" ] || break
		stats_str=$(msgfmt --statistics $i 2>&1 >/dev/null)
		read -r -a stats_arr <<< "$stats_str"

		correct=$(echo ${stats_arr[0]}| grep -Eo "[[:digit:]]*")
		fuzzy=$(echo ${stats_arr[1]}| grep -Eo "[[:digit:]]*")
		untranslated=$(echo ${stats_arr[2]}| grep -Eo "[[:digit:]]*")
		: ${correct:=0}
		: ${fuzzy:=0}
		: ${untranslated:=0}

		echo "| ${i%%\.*} | $correct | $fuzzy | $untranslated |"
	done
	cd ..

	IFS=$old_ifs
}

################################################################################

function relative_percentages () {
	echo "| language | completion percentage |"
	echo "|----------|-----------------------|"

	old_ifs=$IFS
	IFS=','

	cd po
	for i in *.po; do
		[ -f "$i" ] || break
		stats_str=$(msgfmt --statistics $i 2>&1 >/dev/null)
		read -r -a stats_arr <<< "$stats_str"

		correct=$(echo ${stats_arr[0]}| grep -Eo "[[:digit:]]*")
		fuzzy=$(echo ${stats_arr[1]}| grep -Eo "[[:digit:]]*")
		untranslated=$(echo ${stats_arr[2]}| grep -Eo "[[:digit:]]*")
		: ${correct:=0}
		: ${fuzzy:=0}
		: ${untranslated:=0}

		total=$(($correct + $fuzzy + $untranslated))
		percentage=$(($correct * 100 /$total))
		echo "| ${i%%\.*} | $percentage% |"
	done
	cd ..

	IFS=$old_ifs
}

################################################################################

if [ $# = 0 ]; then
	echo "Available methods:"
	declare -F
	echo ""
	echo "Running relative_percentages by default"
	relative_percentages
else
	$1 $2
fi

exit 0

