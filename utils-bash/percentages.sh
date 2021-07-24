#!/bin/bash

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
	echo "| ${i%%\.*} | $correct | $fuzzy | $untranslated |"
done
cd ..

