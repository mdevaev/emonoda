# Contributor: Devaev Maxim <mdevaev@gmail.com>
# Author: Devaev Maxim <mdevaev@gmail.com>


pkgname="emonoda"
pkgver="2.1.25"
pkgrel="1"
pkgdesc="A set of tools to organize and manage your torrents"
arch=("any")
url="https://github.com/mdevaev/emonoda"
license=("GPL")
depends=(
	"python"
	"python-chardet"
	"python-yaml"
	"python-colorama"
	"python-pygments"
	"python-mako"
	"python-pytz"
	"python-dateutil"
)
optdepends=(
	"python-transmissionrpc: Transmission support"
	"python-dbus: KTorrent support"
)
makedepends=("python-setuptools" "cython" "wget")
source=(
    "${pkgname}-${pkgver}.tar.gz"::${url}/archive/v${pkgver}.tar.gz
)
sha256sums=('43e17d16c59c870696ee56e193a171033c60f9ce55a76ffb6e878d498bb9d356')

build() {
	cd "${srcdir}/${pkgname}-${pkgver}"
	python setup.py build
}

package() {
	cd "${srcdir}/${pkgname}-${pkgver}"
	python setup.py install --root="${pkgdir}"
}
