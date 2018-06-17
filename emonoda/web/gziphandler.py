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


from urllib.request import BaseHandler
from urllib.request import Request

from urllib.response import addinfo  # type: ignore
from urllib.response import addinfourl

import gzip

from typing import Union


# =====
class GzipHandler(BaseHandler):
    def http_request(self, request: Request) -> Request:
        request.add_header("Accept-Encoding", "gzip")
        return request

    def http_response(self, request: Request, response: addinfo) -> Union[addinfo, addinfourl]:  # pylint: disable=unused-argument
        if response.headers.get("Content-Encoding") == "gzip":
            gzip_file = gzip.GzipFile(fileobj=response, mode="r")
            new_response = addinfourl(gzip_file, response.headers, response.url, response.code)  # type: ignore
            new_response.msg = response.msg  # type: ignore
            return new_response
        return response

    https_request = http_request
    https_response = http_response

    # XXX: vulture hacks
    _ = https_request
    _ = https_response  # type: ignore
    del _
