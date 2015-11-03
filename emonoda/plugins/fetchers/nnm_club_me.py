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
def _encode(arg):
    return arg.encode("cp1251")


def _decode(arg):
    return arg.decode("cp1251")


class Plugin(BaseFetcher, WithLogin, WithScrape):
    _domain = "nnm-club.me"

    def __init__(self, **kwargs):  # pylint: disable=super-init-not-called
        self._init_bases(**kwargs)
        self._init_opener(with_cookies=True)
        self._comment_regexp = re.compile(r"http://nnm-club\.(me|ru)/forum/viewtopic\.php\?p=(\d+)")

    @classmethod
    def get_name(cls):
        return "nnm-club.me"

    @classmethod
    def get_version(cls):
        return 1

    @classmethod
    def get_fingerprint(cls):
        return {
            "url":      "http://{}".format(cls._domain),
            "encoding": "cp1251",
            "text":     "<link rel=\"canonical\" href=\"http://nnm-club.me/\">",
        }

    @classmethod
    def get_options(cls):
        return cls._get_merged_options()

    # ===

    def is_torrent_changed(self, torrent):
        return self._is_torrent_registered("http://bt.{}:2710".format(self._domain), torrent)

    def fetch_new_data(self, torrent):
        self._assert_match(torrent)
        page = _decode(self._read_url(torrent.get_comment().replace("nnm-club.ru", "nnm-club.me")))

        torrent_id_match = re.search(r"filelst.php\?attach_id=([a-zA-Z0-9]+)", page)
        self._assert_logic(torrent_id_match is not None, "Unknown torrent_id")
        torrent_id = torrent_id_match.group(1)

        data = self._read_url("http://{}//forum/download.php?id={}".format(self._domain, torrent_id))
        self._assert_valid_data(data)
        return data

    # ===

    def login(self):
        self._assert_auth(self._user is not None, "Required user for site")
        self._assert_auth(self._passwd is not None, "Required password for site")
        post = {
            "username": _encode(self._user),
            "password": _encode(self._passwd),
            "redirect": b"",
            "login":    b"\xc2\xf5\xee\xe4",
        }
        page = _decode(self._read_url(
            url="http://{}/forum/login.php".format(self._domain),
            data=_encode(urllib.parse.urlencode(post)),
        ))
        self._assert_auth("[ {} ]".format(self._user) in page, "Invalid user or password")
