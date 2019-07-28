#!/bin/bash

DISTRO="unstable" # TODO lister les valeurs possibles (debian ? ubuntu ? elementary ?)
PACKAGE_NAME="drawing" # TODO et pour elementary ?
VERSION="0.4"

# se souvenir du dossier courant (qui est la racine du projet)
previous_dir=`pwd`

# mettre en place la structure à la con voulue par les scripts de debian
DIR_NAME=$PACKAGE_NAME'-'$VERSION
FILE_NAME=$PACKAGE_NAME'_'$VERSION
DIR_PATH=/tmp/building-dir
mkdir -p $DIR_PATH/$DIR_NAME/
cp -r build-aux $DIR_PATH/$DIR_NAME/
cp -r data $DIR_PATH/$DIR_NAME/
cp -r debian $DIR_PATH/$DIR_NAME/
cp -r help $DIR_PATH/$DIR_NAME/
cp -r po $DIR_PATH/$DIR_NAME/
cp -r src $DIR_PATH/$DIR_NAME/
cp meson.build $DIR_PATH/$DIR_NAME/
cd $DIR_PATH/
tar -Jcvf $FILE_NAME.orig.tar.xz $DIR_NAME
# tar -Jcvf $PACKAGE_NAME.orig.tar.xz $DIR_NAME
cd $DIR_PATH/$DIR_NAME/

# création des fichiers exigés
## création de 'control' à partir des appdata
# TODO

## création de 'changelog' à partir des appdata
# TODO

## création de 'compat'
echo '10' > $DIR_PATH/$DIR_NAME/debian/compat

# le truc qui chie des fichiers supplémentaires pour la construction
dh_make -i -y

# la construction
debuild -i -us -uc -b

# récupérer le paquet dans /tmp
cp $DIR_PATH/*.deb $previous_dir

# nettoyage
ls $DIR_PATH
ls $DIR_PATH/$DIR_NAME
rm -r $DIR_PATH
cd $previous_dir

