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

from . import BaseTracker
from . import WithLogin
from . import WithSimplePostLogin
from . import WithScrape
from . import WithDownloadId


# =====
class Plugin(BaseTracker, WithLogin, WithSimplePostLogin, WithScrape, WithDownloadId):
    PLUGIN_NAME = _DOMAIN = "nnm-club.me"

    _SITE_VERSION = 1
    _SITE_ENCODING = "cp1251"

    _SITE_FINGERPRINT_URL = "http://{}".format(_DOMAIN)
    _SITE_FINGERPRINT_TEXT = "<link rel=\"canonical\" href=\"http://nnm-club.me/\">"

    _COMMENT_REGEXP = re.compile(r"http://nnm-club\.(me|ru)/forum/viewtopic\.php\?p=(\d+)")

    _SCRAPE_URL = "http://bt.{}:2710/scrape.php?info_hash={{scrape_hash}}".format(_DOMAIN)

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
        return self._fetch_data_by_id(
            url=torrent.get_comment().replace("nnm-club.ru", "nnm-club.me"),
            dl_id_regexp=re.compile(r"filelst.php\?attach_id=([a-zA-Z0-9]+)"),
            dl_id_url="http://{}//forum/download.php?id={{dl_id}}".format(self._DOMAIN),
        )

    def login(self):
        self._simple_post_login(
            url="http://{}/forum/login.php".format(self._DOMAIN),
            post={
                "username": self._encode(self._user),
                "password": self._encode(self._passwd),
                "redirect": b"",
                "login":    b"\xc2\xf5\xee\xe4",
            },
            ok_text="class=\"mainmenu\">Выход [ {} ]</a>".format(self._user),
        )
