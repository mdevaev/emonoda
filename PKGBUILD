# Contributor: Devaev Maxim <mdevaev@gmail.com>
# Author: Devaev Maxim <mdevaev@gmail.com>

pkgname=rtfetch
pkgver="0.16"
pkgrel=1
pkgdesc="The set of tools to organize and management of your torrents"
arch=('any')
url="http://github.com/mdevaev/rtfetch.git"
license="GPL"
depends=('python' 'python-ulib-git>=0.7')
optdepends=(
	'python-pysocks-git: SOCKS4/5-proxy support'
	'python-transmissionrpc: Transmission support'
	'python-dbus: KTorrent support'
)
makedepends=('python-setuptools' 'git')

_gitroot="git://github.com/mdevaev/rtfetch.git"
_gitname="rtfetch"


build() {
	cd $startdir/src
	if [ -d $_gitname ]; then
		msg "Updating local repository..."
		cd $_gitname
		git pull origin master || return 1
		msg "The local files are updated."
		cd ..
	else
		git clone --branch=v$pkgver --depth=1 $_gitroot
	fi

	msg "Git clone done or server timeout"
	msg "Starting make..."

	rm -rf $_gitname-build
	cp -r $_gitname $_gitname-build
	cd $_gitname-build

	python setup.py build
}

package() {
	cd $startdir/src/$_gitname-build
	python setup.py install --root="$pkgdir" --prefix=/usr
	mv $pkgdir/usr/bin/rtfetch.py $pkgdir/usr/bin/rtfetch
	mv $pkgdir/usr/bin/rtload.py $pkgdir/usr/bin/rtload
	mv $pkgdir/usr/bin/rtfile.py $pkgdir/usr/bin/rtfile
	mv $pkgdir/usr/bin/rtdiff.py $pkgdir/usr/bin/rtdiff
	mv $pkgdir/usr/bin/rthook-manage-trackers.py $pkgdir/usr/bin/rthook-manage-trackers
}

