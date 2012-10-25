# Contributor: Devaev Maxim <mdevaev@gmail.com>

pkgname=rtfetch
pkgver=20121025
pkgrel=1
pkgdesc="Update rtorrent files from rutracker.org"
arch=('any')
url="http://github.com/mdevaev/rtfetch.git"
license="GPL"
depends=('python2' 'python2-bencode')
makedepends=('git')

_gitroot="git://github.com/mdevaev/rtfetch.git"
_gitname="rtfetch"


build() {
	cd $startdir/src
	if [ -d $_gitname ]; then
		msg "Updateing local repository..."
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

	make DESTDIR=$pkgdir install
}

