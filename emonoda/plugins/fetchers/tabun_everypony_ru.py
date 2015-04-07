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
    return arg.encode("utf-8")


def _decode(arg):
    return arg.decode("utf-8")


class Plugin(BaseFetcher, WithLogin):
    def __init__(self, **kwargs):  # pylint: disable=super-init-not-called
        self._init_bases(**kwargs)
        self._init_opener(with_cookies=True)
        self._comment_regexp = re.compile(r"http://tabun\.everypony\.ru/blog/torrents/(\d+)\.html")
        self._last_data = None

    @classmethod
    def get_name(cls):
        return "tabun.everypony.ru"

    @classmethod
    def get_version(cls):
        return 0

    @classmethod
    def get_fingerprint(cls):
        return {
            "url":      "http://tabun.everypony.ru",
            "encoding": "utf-8",
            "text":     "<link href=\"http://tabun.everypony.ru/templates/skin/synio/images/favicon.ico?v1\" "
                        "rel=\"shortcut icon\" />",
        }

    @classmethod
    def get_options(cls):
        return cls._get_merged_options()

    # ===

    def is_torrent_changed(self, torrent):
        self._last_data = None
        self._assert_match(torrent)
        candidate = self._get_candidate(torrent)
        if torrent.get_hash() != candidate.get_hash():
            self._last_data = candidate.get_data()
            return True
        return False

    def _get_candidate(self, torrent):
        download_id = self._comment_regexp.match(torrent.get_comment()).group(1)
        data = self._read_url("http://tabun.everypony.ru/file/go/{}/".format(download_id))
        self._assert_valid_data(data)
        candidate = tfile.Torrent(data=data)
        return candidate

    def fetch_new_data(self, torrent):
        return self._last_data

    # ===

    def login(self):
        self._assert_auth(self._passwd is not None, "Required passwd for tabun.everypony.ru")

        page = _decode(self._read_url("http://tabun.everypony.ru"))
        key_match = re.search(r"var LIVESTREET_SECURITY_KEY = '([0-9a-fA-F]+)';", page)
        self._assert_auth(key_match is not None, "Unknown LIVESTREET_SECURITY_KEY")
        key = key_match.group(1)

        post = {
            "login":           _encode(self._user),
            "password":        _encode(self._passwd),
            "remember":        b"on",
            "security_ls_key": _encode(key),
        }
        post_data = _encode(urllib.parse.urlencode(post))
        page = _decode(self._read_url(
            url="http://tabun.everypony.ru/login/ajax-login/",
            data=post_data,
            headers={"Referer": "http://tabun.everypony.ru/"},
        ))
        self._assert_auth("\"bStateError\":false" in page, "Invalid login or password")
