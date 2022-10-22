#!/bin/bash
# Licensed under GPL3 https://github.com/maoschanz/drawing/blob/master/LICENSE

DISTRO="unstable" # this script is for local use, distros manage this themselves
PACKAGE_NAME="drawing"
VERSION="1.0.1" # XXX ask it as an input maybe?

function separator () {
	echo ""
	echo "---------------------------------------------------------------------"
	echo ""
}

echo "targeted distribution: $DISTRO"
echo "package name: $PACKAGE_NAME"
echo "package version: $VERSION"
echo ""
echo "Is it correct? [Return/^C]"
read confirmation
separator

# remember current directory (theoretically, the project's root) to bring the
# package here in the end
previous_dir=`pwd`

# set up the stupidly specific structure required by debian scripts
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
cp meson_options.txt $DIR_PATH/$DIR_NAME/
cd $DIR_PATH/
tar -Jcvf $FILE_NAME.orig.tar.xz $DIR_NAME
cd $DIR_PATH/$DIR_NAME/
separator

# automatic creation of additional files for the build process
dh_make -i -y
separator

# actually building the package
dpkg-buildpackage -i -us -uc -b
separator

# get the package in /tmp and move it where the user is
cp $DIR_PATH/*.deb $previous_dir

# cleaning
ls $DIR_PATH
ls $DIR_PATH/$DIR_NAME
rm -r $DIR_PATH
cd $previous_dir

