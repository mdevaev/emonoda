# Contributor: Devaev Maxim <mdevaev@gmail.com>

pkgname=rtfetch
pkgver="0.1"
pkgrel=1
pkgdesc="The set of tools to organize and management of your torrents"
arch=('any')
url="http://github.com/mdevaev/rtfetch.git"
license="GPL"
depends=('python2' 'python2-bencode' 'python2-ulib-git>=0.1')
makedepends=('git')

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
		git clone $_gitroot --depth=1
	fi

	msg "Git clone done or server timeout"
	msg "Starting make..."

	rm -rf $_gitname-build
	cp -r $_gitname $_gitname-build
	cd $_gitname-build

	python2 setup.py install --root="$pkgdir" --prefix=/usr
	mv $pkgdir/usr/bin/rtfetch.py $pkgdir/usr/bin/rtfetch
	mv $pkgdir/usr/bin/rtquery.py $pkgdir/usr/bin/rtquery
	mv $pkgdir/usr/bin/rtload.py $pkgdir/usr/bin/rtload
	mv $pkgdir/usr/bin/rtfile.py $pkgdir/usr/bin/rtfile
	mv $pkgdir/usr/bin/rtdiff.py $pkgdir/usr/bin/rtdiff
	mv $pkgdir/usr/bin/rthook-manage-trackers.py $pkgdir/usr/bin/rthook-manage-trackers
}

