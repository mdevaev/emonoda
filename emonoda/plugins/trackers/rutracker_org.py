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

from . import BaseTracker
from . import WithLogin
from . import WithCaptcha
from . import WithCheckHash
from . import WithFetchCustom


# =====
class Plugin(BaseTracker, WithLogin, WithCaptcha, WithCheckHash, WithFetchCustom):
    PLUGIN_NAME = "rutracker.org"

    _SITE_VERSION = 4
    _SITE_ENCODING = "cp1251"
    _SITE_RETRY_CODES = (503, 404)

    _SITE_FINGERPRINT_URL = "https://rutracker.org/forum/index.php"
    _SITE_FINGERPRINT_TEXT = "href=\"//static.t-ru.org/favicon.ico\" type=\"image/x-icon\""

    _COMMENT_REGEXP = re.compile(r"https?://rutracker\.org/forum/viewtopic\.php\?t=(?P<torrent_id>\d+)")

    _TORRENT_HASH_URL = "https://rutracker.org/forum/viewtopic.php?t={torrent_id}"
    _TORRENT_HASH_REGEXP = re.compile(r"<span id=\"tor-hash\">(?P<torrent_hash>[a-fA-F0-9]{40})</span>")

    def __init__(self, **kwargs):  # pylint: disable=super-init-not-called
        self._init_bases(**kwargs)
        self._init_opener(with_cookies=True)

    @classmethod
    def get_options(cls):
        return cls._get_merged_options()

    # ===

    def fetch_new_data(self, torrent):
        self._assert_match(torrent)
        torrent_id = self._COMMENT_REGEXP.match(torrent.get_comment()).group("torrent_id")
        self._cookie_jar.set_cookie(http.cookiejar.Cookie(
            version=0,
            name="bb_dl",
            value=torrent_id,
            port=None,
            port_specified=False,
            domain="",
            domain_specified=False,
            domain_initial_dot=False,
            path="/forum/",
            path_specified=True,
            secure=True,
            expires=None,
            discard=True,
            comment=None,
            comment_url=None,
            rest={"HttpOnly": None},
            rfc2109=False,
        ))
        data = self._read_url(
            url="https://rutracker.org/forum/dl.php?t={}".format(torrent_id),
            data=b"",
            headers={
                "Referer": "https://rutracker.org/forum/viewtopic.php?t={}".format(torrent_id),
                "Origin":  "https://rutracker.org",
            }
        )
        self._assert_valid_data(data)
        return data

    def login(self):
        self._assert_required_user_passwd()

        post = {
            "login_username": self._encode(self._user),
            "login_password": self._encode(self._passwd),
            "login":          b"\xc2\xf5\xee\xe4",
        }
        page = self._read_login(post)

        cap_static_regexp = re.compile(r"\"//(static\.t-ru\.org/captcha/[^\"]+)\"")
        cap_static_match = cap_static_regexp.search(page)
        if cap_static_match is not None:
            cap_sid_match = re.search(r"name=\"cap_sid\" value=\"([a-zA-Z0-9]+)\"", page)
            cap_code_match = re.search(r"name=\"(cap_code_[a-zA-Z0-9]+)\"", page)
            self._assert_auth(cap_sid_match is not None, "Unknown cap_sid")
            self._assert_auth(cap_code_match is not None, "Unknown cap_code")

            post[cap_code_match.group(1)] = self._captcha_decoder("https://{}".format(cap_static_match.group(1)))
            post["cap_sid"] = cap_sid_match.group(1)
            page = self._read_login(post)
            self._assert_auth(cap_static_regexp.search(page) is None, "Invalid user, password or captcha")

    def _read_login(self, post):
        return self._decode(self._read_url(
            url="https://rutracker.org/forum/login.php",
            data=self._encode(urllib.parse.urlencode(post)),
        ))
