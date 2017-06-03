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
class SocksHandler(urllib.request.HTTPHandler, urllib.request.HTTPSHandler):
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        super().__init__(debuglevel=kwargs.pop("debuglevel", 0))

    def http_open(self, req):
        def build(host, port=None, strict=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT):  # pylint: disable=protected-access
            connection = _SocksConnection(host, port=port, strict=strict, timeout=timeout, **self._kwargs)
            connection.make_proxy_args(*self._args, **self._kwargs)
            return connection
        return self.do_open(build, req)

    def https_open(self, req):
        def build(host, port=None, strict=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT):  # pylint: disable=protected-access
            connection = _SocksSecureConnection(host, port=port, strict=strict, timeout=timeout, **self._kwargs)
            connection.make_proxy_args(*self._args, **self._kwargs)
            return connection
        return self.do_open(build, req)


# =====
class _SocksConnection(http.client.HTTPConnection):
    def __init__(self, *args, **kwargs):
        kwargs.pop("strict", None)  # XXX: Fix for "TypeError: __init__() got an unexpected keyword argument 'strict'"
        kwargs.pop("proxy_url", None)  # XXX: Fix for "TypeError: __init__() got an unexpected keyword argument 'proxy_url'"
        super().__init__(*args, **kwargs)
        self._proxy_args = None

    # XXX: because proxy args/kwargs break super
    def make_proxy_args(
        self,
        proxy_url=None,
        proxy_type=None,
        proxy_host=None,
        proxy_port=None,
        proxy_user=None,
        proxy_passwd=None,
        rdns=True
    ):
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
        if self._proxy_args is None:
            raise RuntimeError("Proxy args weren't initialized")
        self.sock = socks.socksocket()
        self.sock.setproxy(*self._proxy_args)
        if self.timeout is not socket._GLOBAL_DEFAULT_TIMEOUT:  # pylint: disable=protected-access
            self.sock.settimeout(self.timeout)
        self.sock.connect((self.host, self.port))


# =====
class _SocksSecureConnection(http.client.HTTPSConnection, _SocksConnection):
    def __init__(self, *args, **kwargs):
        kwargs.pop("strict", None)  # XXX: Fix for "TypeError: __init__() got an unexpected keyword argument 'strict'"
        kwargs.pop("proxy_url", None)  # XXX: Fix for "TypeError: __init__() got an unexpected keyword argument 'proxy_url'"
        super().__init__(*args, **kwargs)
