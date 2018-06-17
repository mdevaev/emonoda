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


import socket
import urllib.parse

from urllib.request import HTTPHandler
from urllib.request import HTTPSHandler
from urllib.request import Request

from http.client import HTTPConnection
from http.client import HTTPSConnection
from http.client import HTTPResponse

from typing import Tuple
from typing import Optional
from typing import Any

from ..thirdparty import socks


# =====
SCHEME_TO_TYPE = {
    "socks4": socks.PROXY_TYPE_SOCKS4,
    "socks5": socks.PROXY_TYPE_SOCKS5,
}

SOCKS_PORT = 1080


# =====
class _SocksConnection(HTTPConnection):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.pop("proxy_url", None)  # XXX: Fix for "TypeError: __init__() got an unexpected keyword argument 'proxy_url'"
        super().__init__(*args, **kwargs)
        self.__proxy_args: Optional[Tuple[
            Optional[int],
            Optional[str],
            Optional[int],
            bool,
            Optional[str],
            Optional[str],
        ]] = None

    # XXX: because proxy args/kwargs break super
    def make_proxy_args(
        self,
        proxy_url: str="",
        proxy_type: Optional[int]=None,
        proxy_host: Optional[str]=None,
        proxy_port: Optional[int]=None,
        proxy_user: Optional[str]=None,
        proxy_passwd: Optional[str]=None,
        rdns: bool=True,
    ) -> None:

        if proxy_url:
            parsed = urllib.parse.urlparse(proxy_url)
            scheme = parsed.scheme
            proxy_user = parsed.username
            proxy_passwd = parsed.password
            proxy_host = parsed.hostname
            proxy_port = (parsed.port or SOCKS_PORT)
            proxy_type = SCHEME_TO_TYPE.get((scheme or "").lower())
            if proxy_type is None:
                raise RuntimeError("Invalid SOCKS protocol: {}".format(scheme))

        self.__proxy_args = (proxy_type, proxy_host, proxy_port, rdns, proxy_user, proxy_passwd)

    def connect(self) -> None:
        assert self.__proxy_args is not None, "Proxy args weren't initialized"
        self.sock = socks.socksocket()
        self.sock.setproxy(*self.__proxy_args)
        timeout = self.timeout  # type: ignore
        if timeout is not socket._GLOBAL_DEFAULT_TIMEOUT:  # pylint: disable=protected-access
            self.sock.settimeout(timeout)
        self.sock.connect((self.host, self.port))  # type: ignore


class _SocksSecureConnection(HTTPSConnection, _SocksConnection):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.pop("proxy_url", None)  # XXX: Fix for "TypeError: __init__() got an unexpected keyword argument 'proxy_url'"
        super().__init__(*args, **kwargs)


# =====
class SocksHandler(HTTPHandler, HTTPSHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.__args = args
        self.__kwargs = kwargs
        super().__init__(debuglevel=kwargs.pop("debuglevel", 0))

    def http_open(self, req: Request) -> HTTPResponse:
        def build(
            host: str,
            port: Optional[int]=None,
            timeout: int=socket._GLOBAL_DEFAULT_TIMEOUT,  # pylint: disable=protected-access
        ) -> _SocksConnection:

            connection = _SocksConnection(host, port=port, timeout=timeout, **self.__kwargs)
            connection.make_proxy_args(*self.__args, **self.__kwargs)
            return connection

        return self.do_open(build, req)  # type: ignore

    def https_open(self, req: Request) -> HTTPResponse:
        def build(
            host: str,
            port: Optional[int]=None,
            timeout: int=socket._GLOBAL_DEFAULT_TIMEOUT,  # pylint: disable=protected-access
        ) -> _SocksSecureConnection:

            connection = _SocksSecureConnection(host, port=port, timeout=timeout, **self.__kwargs)
            connection.make_proxy_args(*self.__args, **self.__kwargs)
            return connection

        return self.do_open(build, req)  # type: ignore

    # XXX: vulture hacks
    _ = http_open
    _ = https_open
    del _
