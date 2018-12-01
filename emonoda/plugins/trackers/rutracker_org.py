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


import re

from typing import Dict
from typing import Any

from ...optconf import Option

from ...tfile import Torrent

from . import WithLogin
from . import WithCaptcha
from . import WithCheckHash
from . import WithStat


# =====
class Plugin(WithLogin, WithCaptcha, WithCheckHash, WithStat):
    PLUGIN_NAMES = [
        "rutracker.org",
        "torrents.ru",
    ]

    _SITE_VERSION = 6
    _SITE_ENCODING = "cp1251"
    _SITE_RETRY_CODES = [503, 404]

    _SITE_FINGERPRINT_URL = "https://rutracker.org/forum/index.php"
    _SITE_FINGERPRINT_TEXT = ("<link rel=\"search\" type=\"application/opensearchdescription+xml\""
                              " title=\"Поиск на RuTracker.org\" href=\"https://static.t-ru.org/opensearch.xml\">")

    _COMMENT_REGEXP = re.compile(r"https?://rutracker\.org/forum/viewtopic\.php\?t=(?P<torrent_id>\d+)")

    _TORRENT_HASH_URL = "https://rutracker.org/forum/viewtopic.php?t={torrent_id}"
    _TORRENT_HASH_REGEXP = re.compile(r"<span id=\"tor-hash\">(?P<torrent_hash>[a-fA-F0-9]{40})</span>")

    _STAT_URL = _TORRENT_HASH_URL
    _STAT_OK_REGEXP = _TORRENT_HASH_REGEXP
    _STAT_SEEDERS_REGEXP = re.compile(r"<span class=\"seed\">Сиды:&nbsp;\s+<b>(?P<seeders>\d+)</b></span>")
    _STAT_LEECHERS_REGEXP = re.compile(r"<span class=\"leech\">Личи:&nbsp;\s+<b>(?P<leechers>\d+)</b></span>")

    # =====

    def __init__(self, **kwargs: Any) -> None:  # pylint: disable=super-init-not-called
        self._init_bases(**kwargs)
        self._init_opener(with_cookies=True)

    @classmethod
    def get_options(cls) -> Dict[str, Option]:
        return cls._get_merged_options()

    def fetch_new_data(self, torrent: Torrent) -> bytes:
        torrent_id = self._assert_match(torrent)
        self._set_cookie("bb_dl", torrent_id, path="/forum/", secure=True)
        return self._assert_valid_data(self._read_url(
            url="https://rutracker.org/forum/dl.php?t={}".format(torrent_id),
            data=b"",
            headers={
                "Referer": "https://rutracker.org/forum/viewtopic.php?t={}".format(torrent_id),
                "Origin":  "https://rutracker.org",
            }
        ))

    def login(self) -> None:
        self._assert_required_user_passwd()

        post = {
            "login_username": self._encode(self._user),
            "login_password": self._encode(self._passwd),
            "login":          b"\xc2\xf5\xee\xe4",
        }
        page = self.__read_login(post)

        cap_static_regexp = re.compile(r"\"//(static\.t-ru\.org/captcha/[^\"]+)\"")
        cap_static_match = cap_static_regexp.search(page)
        if cap_static_match is not None:
            cap_sid = self._assert_auth_re_search(
                regexp=re.compile(r"name=\"cap_sid\" value=\"([a-zA-Z0-9]+)\""),
                text=page,
                msg="Unknown cap_sid",
            ).group(1)

            cap_code = self._assert_auth_re_search(
                regexp=re.compile(r"name=\"(cap_code_[a-zA-Z0-9]+)\""),
                text=page,
                msg="Unknown cap_code",
            ).group(1)

            post[cap_code] = self._encode(self._captcha_decoder("https://{}".format(cap_static_match.group(1))))
            post["cap_sid"] = self._encode(cap_sid)

            page = self.__read_login(post)
            self._assert_auth(cap_static_regexp.search(page) is None, "Invalid user, password or captcha")

    def __read_login(self, post: Dict[str, bytes]) -> str:
        return self._decode(self._read_url(
            url="https://rutracker.org/forum/login.php",
            data=self._urlencode(post),
        ))
