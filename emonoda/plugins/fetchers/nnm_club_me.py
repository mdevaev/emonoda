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

from ... import tfile

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
            "url":      "http://nnm-club.me",
            "encoding": "cp1251",
            "text":     "<link rel=\"canonical\" href=\"http://nnm-club.me/\">",
        }

    @classmethod
    def get_options(cls):
        return cls._get_merged_options()

    # ===

    def is_torrent_changed(self, torrent):
        self._assert_match(torrent)
        data = self._read_url(
            url="http://bt.nnm-club.me:2710/scrape?info_hash={}".format(torrent.get_scrape_hash()),
            headers={"User-Agent": self._client_agent},
        )
        return (len(tfile.decode_data(data).get("files", {})) == 0)

    def fetch_new_data(self, torrent):
        self._assert_match(torrent)
        page = _decode(self._read_url(torrent.get_comment().replace("nnm-club.ru", "nnm-club.me")))

        torrent_id_match = re.search(r"filelst.php\?attach_id=([a-zA-Z0-9]+)", page)
        self._assert_logic(torrent_id_match is not None, "Unknown torrent_id")
        torrent_id = torrent_id_match.group(1)

        data = self._read_url("http://nnm-club.me//forum/download.php?id={}".format(torrent_id))
        self._assert_valid_data(data)
        return data

    # ===

    def login(self):
        self._assert_auth(self._user is not None, "Required user nnmclub")
        self._assert_auth(self._passwd is not None, "Required passwd nnmclub")
        post = {
            "username": _encode(self._user),
            "password": _encode(self._passwd),
            "redirect": b"",
            "login":    b"\xc2\xf5\xee\xe4",
        }
        page = _decode(self._read_url(
            url="http://nnm-club.me/forum/login.php",
            data=_encode(urllib.parse.urlencode(post)),
        ))
        self._assert_auth("[ {} ]".format(self._user) in page, "Invalid login or password")
