"""
    Emonoda -- A set of tools to organize and manage your torrents
    Copyright (C) 2015  Devaev Maxim <mdevaev@gmail.com>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


import urllib.request
import urllib.parse
import http.client
import socket

from ..thirdparty import socks


# =====
SCHEME_TO_TYPE = {
    "socks4": socks.PROXY_TYPE_SOCKS4,
    "socks5": socks.PROXY_TYPE_SOCKS5,
}

SOCKS_PORT = 1080


# =====
class SocksHandler(urllib.request.HTTPHandler):
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        super().__init__(debuglevel=kwargs.pop("debuglevel", 0))

    def http_open(self, request):
        def build(host, port=None, strict=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT):  # pylint: disable=protected-access
            return _SocksConnection(*self._args, host=host, port=port, strict=strict, timeout=timeout, **self._kwargs)
        return self.do_open(build, request)


# =====
class _SocksConnection(http.client.HTTPConnection):
    def __init__(
        self,
        proxy_url=None,
        proxy_type=None,
        proxy_host=None,
        proxy_port=None,
        proxy_user=None,
        proxy_passwd=None,
        rdns=True,
        *args,
        **kwargs
    ):
        kwargs.pop("strict", None)  # XXX: Fix for "TypeError: __init__() got an unexpected keyword argument 'strict'"
        super().__init__(*args, **kwargs)

        if proxy_url is not None:
            parsed = urllib.parse.urlparse(proxy_url)
            scheme = parsed.scheme
            proxy_user = parsed.username
            proxy_passwd = parsed.password
            proxy_host = parsed.hostname
            proxy_port = (parsed.port or SOCKS_PORT)
            proxy_type = SCHEME_TO_TYPE.get((scheme or "").lower())
            if proxy_type is None:
                raise RuntimeError("Invalid SOCKS protocol: {}".format(scheme))

        self._proxy_args = (proxy_type, proxy_host, proxy_port, rdns, proxy_user, proxy_passwd)

    def connect(self):
        self.sock = socks.socksocket()
        self.sock.setproxy(*self._proxy_args)
        if self.timeout is not socket._GLOBAL_DEFAULT_TIMEOUT:  # pylint: disable=protected-access
            self.sock.settimeout(self.timeout)
        self.sock.connect((self.host, self.port))
