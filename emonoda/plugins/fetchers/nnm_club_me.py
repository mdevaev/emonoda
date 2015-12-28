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
import re

from . import BaseFetcher
from . import WithLogin
from . import WithScrape


# =====
class Plugin(BaseFetcher, WithLogin, WithScrape):
    PLUGIN_NAME = _DOMAIN = "nnm-club.me"

    _SITE_VERSION = 1
    _SITE_ENCODING = "cp1251"

    _SITE_FINGERPRINT_URL = "http://{}".format(_DOMAIN)
    _SITE_FINGERPRINT_TEXT = "<link rel=\"canonical\" href=\"http://nnm-club.me/\">"

    _COMMENT_REGEXP = re.compile(r"http://nnm-club\.(me|ru)/forum/viewtopic\.php\?p=(\d+)")

    _BASE_SCRAPE_URL = "http://bt.{}:2710".format(_DOMAIN)

    # ===

    def __init__(self, **kwargs):  # pylint: disable=super-init-not-called
        self._init_bases(**kwargs)
        self._init_opener(with_cookies=True)

    @classmethod
    def get_options(cls):
        return cls._get_merged_options()

    # ===

    def fetch_new_data(self, torrent):
        self._assert_match(torrent)
        page = self._decode(self._read_url(torrent.get_comment().replace("nnm-club.ru", "nnm-club.me")))

        torrent_id_match = re.search(r"filelst.php\?attach_id=([a-zA-Z0-9]+)", page)
        self._assert_logic(torrent_id_match is not None, "Unknown torrent_id")
        torrent_id = torrent_id_match.group(1)

        data = self._read_url("http://{}//forum/download.php?id={}".format(self._DOMAIN, torrent_id))
        self._assert_valid_data(data)
        return data

    # ===

    def login(self):
        self._assert_auth(self._user is not None, "Required user for site")
        self._assert_auth(self._passwd is not None, "Required password for site")
        post_data = self._encode(urllib.parse.urlencode({
            "username": self._encode(self._user),
            "password": self._encode(self._passwd),
            "redirect": b"",
            "login":    b"\xc2\xf5\xee\xe4",
        }))
        page = self._decode(self._read_url("http://{}/forum/login.php".format(self._DOMAIN), data=post_data))
        self._assert_auth("[ {} ]".format(self._user) in page, "Invalid user or password")
