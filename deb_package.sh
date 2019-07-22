#!/bin/bash

DISTRO="unstable" # TODO lister les valeurs possibles
PACKAGE_NAME="drawing" # TODO et pour elementary ?
VERSION="0.4"

# se souvenir du dossier courant (qui est la racine du projet)
previous_dir=`pwd`

# mettre en place la structure à la con voulue par les scripts de debian
DIR_NAME=$PACKAGE_NAME'_'$VERSION
mkdir -p /tmp/building-dir/$DIR_NAME
cp -r build-aux /tmp/building-dir/$DIR_NAME
cp -r data /tmp/building-dir/$DIR_NAME
cp -r debian /tmp/building-dir/$DIR_NAME
cp -r help /tmp/building-dir/$DIR_NAME
cp -r po /tmp/building-dir/$DIR_NAME
cp -r src /tmp/building-dir/$DIR_NAME
cp meson.build /tmp/building-dir/$DIR_NAME
cd /tmp/building-dir/
tar -Jcvf $PACKAGE_NAME.orig.tar.xz $DIR_NAME
cd /tmp/building-dir/$DIR_NAME

# création des fichiers exigés
## création de 'control' à partir des appdata
# TODO

## création de 'changelog' à partir des appdata
# TODO

## création de 'compat'
echo '10' > /tmp/building-dir/$DIR_NAME/debian/compat

# le truc qui chie des fichiers supplémentaires pour la construction
dh_make -i

# la construction
debuild -i -us -uc -b

# récupérer le paquet dans /tmp
cp /tmp/building-dir/drawing_0.4_amd64.deb $previous_dir

# nettoyage
# rm -r /tmp/building-dir
cd $previous_dir

