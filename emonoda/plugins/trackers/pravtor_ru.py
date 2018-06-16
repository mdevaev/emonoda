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


import http.cookiejar
import re

from typing import Dict
from typing import Any

from ...optconf import Option

from ...tfile import Torrent

from . import WithLogin
from . import WithCheckHash


# =====
class Plugin(WithLogin, WithCheckHash):
    PLUGIN_NAMES = ["pravtor.ru"]

    _SITE_VERSION = 0
    _SITE_ENCODING = "cp1251"

    _SITE_FINGERPRINT_URL = "http://pravtor.ru"
    _SITE_FINGERPRINT_TEXT = "<img src=\"/images/pravtor_beta1.png\""

    _COMMENT_REGEXP = re.compile(r"http://pravtor\.(ru|spb\.ru)/viewtopic\.php\?p=(?P<torrent_id>\d+)")

    _TORRENT_HASH_URL = "http://pravtor.ru/viewtopic.php?p={torrent_id}"
    _TORRENT_HASH_REGEXP = re.compile(r"<span id=\"tor-hash\">(?P<torrent_hash>[a-zA-Z0-9]+)</span>")

    # ===

    def __init__(self, **kwargs: Any) -> None:  # pylint: disable=super-init-not-called
        self._init_bases(**kwargs)
        self._init_opener(with_cookies=True)

    @classmethod
    def get_options(cls) -> Dict[str, Option]:
        return cls._get_merged_options()

    def fetch_new_data(self, torrent: Torrent) -> bytes:
        torrent_id = self._assert_match(torrent)

        dl_id = self._assert_logic_re_search(
            regexp=re.compile(r"<a href=\"download.php\?id=(\d+)\" class=\"(leech|seed|gen)med\">"),
            text=self._decode(self._read_url(torrent.get_comment())),
            msg="Torrent-ID not found",
        ).group(1)

        self._cookie_jar.set_cookie(http.cookiejar.Cookie(  # type: ignore
            version=0,
            name="bb_dl",
            value=torrent_id,
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
        ))

        return self._assert_valid_data(self._read_url(
            url="http://pravtor.ru/download.php?id={}".format(dl_id),
            data=b"",
            headers={
                "Referer": "http://pravtor.ru/viewtopic.php?t={}".format(torrent_id),
                "Origin":  "http://pravtor.ru",
            }
        ))

    def login(self) -> None:
        self._login_using_post(
            url="http://pravtor.ru/login.php",
            post={
                "login_username": self._encode(self._user),
                "login_password": self._encode(self._passwd),
                "login":          b"\xc2\xf5\xee\xe4",
            },
            ok_text="<b class=\"med\">{}</b></a>&nbsp; [ <a href=\"./login.php?logout=1\"".format(self._user),
        )
