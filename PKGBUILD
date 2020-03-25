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
    "${pkgname}-${pkgver}"::git+${url}#tag=v${pkgver}
)
sha256sums=('SKIP')

build() {
	cd "${srcdir}/${pkgname}-${pkgver}"
	python setup.py build
}

package() {
	cd "${srcdir}/${pkgname}-${pkgver}"
	python setup.py install --root="${pkgdir}"
}
