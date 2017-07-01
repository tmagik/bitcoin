#!/bin/sh -x

NAME=bitcoin-btc1
VERSION=1.14.3
UPSTREAM=${NAME}_${VERSION}.orig.tar.gz

WORKDIR=${1-$PWD/pkg}
if [ ! -d $WORKDIR ]; then
	echo "error: $WORKDIR does not exist"
	exit 1
fi

git archive --format=tar.gz --prefix=bitcoin-btc1/ HEAD > $WORKDIR/$UPSTREAM

cd $WORKDIR
tar zxvf $UPSTREAM
cd bitcoin-btc1
DEB_BUILD_OPTIONS="parallel=4" dpkg-buildpackage
