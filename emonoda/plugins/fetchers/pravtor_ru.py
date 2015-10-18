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


import urllib.parse
import http.cookiejar
import re

from . import BaseFetcher
from . import WithLogin


# =====
def _encode(arg):
    return arg.encode("cp1251")


def _decode(arg):
    return arg.decode("cp1251")


class Plugin(BaseFetcher, WithLogin):
    def __init__(self, **kwargs):  # pylint: disable=super-init-not-called
        self._init_bases(**kwargs)
        self._init_opener(with_cookies=True)
        self._comment_regexp = re.compile(r"http://pravtor\.(ru|spb\.ru)/viewtopic\.php\?p=(\d+)")

    @classmethod
    def get_name(cls):
        return "pravtor.ru"

    @classmethod
    def get_version(cls):
        return 0

    @classmethod
    def get_fingerprint(cls):
        return {
            "url":      "http://pravtor.ru",
            "encoding": "cp1251",
            "text":     "<img src=\"/images/pravtor_beta1.png\"",
        }

    @classmethod
    def get_options(cls):
        return cls._get_merged_options()

    # ===

    def is_torrent_changed(self, torrent):
        self._assert_match(torrent)
        page = _decode(self._read_url(torrent.get_comment()))
        hash_match = re.search(r"<span id=\"tor-hash\">([a-zA-Z0-9]+)</span>", page)
        self._assert_logic(hash_match is not None, "Hash not found")
        return (torrent.get_hash() != hash_match.group(1).lower())

    def fetch_new_data(self, torrent):
        self._assert_match(torrent)

        topic_id = self._comment_regexp.match(torrent.get_comment()).group(1)

        page = _decode(self._read_url(torrent.get_comment()))
        torrent_id_match = re.search(r"<a href=\"download.php\?id=(\d+)\" class=\"(leech|seed|gen)med\">", page)
        self._assert_logic(torrent_id_match is not None, "Torrent-ID not found")
        torrent_id = int(torrent_id_match.group(1))

        cookie = http.cookiejar.Cookie(
            version=0,
            name="bb_dl",
            value=topic_id,
            port=None,
            port_specified=False,
            domain="",
            domain_specified=False,
            domain_initial_dot=False,
            path="/",
            path_specified=True,
            secure=False,
            expires=None,
            discard=True,
            comment=None,
            comment_url=None,
            rest={"HttpOnly": None},
            rfc2109=False,
        )
        self._cookie_jar.set_cookie(cookie)

        data = self._read_url(
            url="http://pravtor.ru/download.php?id={}".format(torrent_id),
            data=b"",
            headers={
                "Referer": "http://pravtor.ru/viewtopic.php?t={}".format(topic_id),
                "Origin":  "http://pravtor.ru",
            }
        )

        self._assert_valid_data(data)
        return data

    # ===

    def login(self):
        self._assert_auth(self._user is not None, "Required user for site")
        self._assert_auth(self._passwd is not None, "Required passwd for site")
        post = {
            "login_username": _encode(self._user),
            "login_password": _encode(self._passwd),
            "login":          b"\xc2\xf5\xee\xe4",
        }
        page = _decode(self._read_url(
            url="http://pravtor.ru/login.php",
            data=_encode(urllib.parse.urlencode(post)),
        ))
        self._assert_auth(re.search(r"<!--login form-->", page) is None, "Invalid user or password")
