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
import urllib.request
import urllib.parse
import urllib.error
import http.client
import http.cookiejar
import io
import time

from typing import Tuple
from typing import List
from typing import Dict
from typing import NamedTuple
from typing import Optional
from typing import Type

from . import gziphandler
from . import sockshandler


# =====
class MultipartFile(NamedTuple):
    name: str
    mimetype: str
    data: bytes


def build_opener(
    proxy_url: str="",
    cookie_jar: Optional[http.cookiejar.CookieJar]=None,
) -> urllib.request.OpenerDirector:

    handlers: List[urllib.request.BaseHandler] = [gziphandler.GzipHandler()]

    if proxy_url:
        scheme = (urllib.parse.urlparse(proxy_url).scheme or "").lower()
        if scheme in ["http", "https"]:
            handlers.append(urllib.request.ProxyHandler({scheme: proxy_url}))
        elif scheme in ["socks4", "socks5"]:
            handlers.append(sockshandler.SocksHandler(proxy_url=proxy_url))
        else:
            raise RuntimeError("Invalid proxy protocol: {}".format(scheme))

    if cookie_jar is not None:
        handlers.append(urllib.request.HTTPCookieProcessor(cookie_jar))

    return urllib.request.build_opener(*handlers)


def read_url(
    opener: urllib.request.OpenerDirector,
    url: str,
    data: Optional[bytes]=None,
    headers: Optional[Dict[str, str]]=None,
    timeout: float=10.0,
    retries: int=10,
    retries_sleep: float=1.0,
    retry_codes: Optional[List[int]]=None,
    retry_timeout: bool=True,
) -> bytes:

    if retry_codes is None:
        retry_codes = [500, 502, 503]

    while True:
        try:
            request = urllib.request.Request(url, data, (headers or {}))
            return opener.open(request, timeout=timeout).read()
        except socket.timeout:
            if retries == 0 or not retry_timeout:
                raise
        except urllib.error.HTTPError as err:
            if retries == 0 or err.code not in retry_codes:
                raise
        except urllib.error.URLError as err:
            if "timed out" in str(err.reason):
                if retries == 0 or not retry_timeout:
                    raise
            else:
                raise
        except (http.client.IncompleteRead, http.client.BadStatusLine, ConnectionResetError):
            if retries == 0:
                raise

        time.sleep(retries_sleep)
        retries -= 1


def encode_multipart(
    fields: Dict[str, str],
    files: Dict[str, MultipartFile],
    encoding: str="utf-8",
    boundary: str="-------------------------acebdf13572468",
) -> Tuple[bytes, Dict[str, str]]:

    data_io = io.BytesIO()

    def write_line(line: str="") -> None:
        data_io.write(line.encode(encoding) + b"\r\n")

    def escape_quote(line: str) -> str:
        return line.replace("\"", "\\\"")

    for (key, value) in fields.items():
        write_line("--{0}".format(boundary))
        write_line("Content-Disposition: form-data; name=\"{0}\"".format(escape_quote(key)))
        write_line()
        write_line(value)

    for (key, mf) in files.items():
        write_line("--{0}".format(boundary))
        write_line("Content-Disposition: form-data; name=\"{0}\"; filename=\"{1}\"".format(
                   escape_quote(key), escape_quote(mf.name)))
        write_line("Content-Type: {0}".format(mf.mimetype))
        write_line()
        data_io.write(mf.data + b"\r\n")

    write_line("--{0}--".format(boundary))

    body = data_io.getvalue()
    headers = {
        "Content-Type": "multipart/form-data; boundary={0}".format(boundary),
        "Content-Length": str(len(body)),
    }
    return (body, headers)
