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

from datetime import datetime

from . import BaseFetcher
from . import WithLogin
from . import WithTime


# =====
def _encode(arg):
    return arg.encode("utf-8")


def _decode(arg):
    return arg.decode("utf-8")


class Plugin(BaseFetcher, WithLogin, WithTime):
    def __init__(self, **kwargs):  # pylint: disable=super-init-not-called
        self._init_bases(**kwargs)
        self._init_opener(with_cookies=True)
        self._comment_regexp = re.compile(r"http://booktracker\.org/viewtopic\.php\?p=(\d+)")
        self._tzinfo = None

    @classmethod
    def get_name(cls):
        return "booktracker.org"

    @classmethod
    def get_version(cls):
        return 0

    @classmethod
    def get_fingerprint(cls):
        return {
            "url":      "http://booktracker.org",
            "encoding": "utf-8",
            "text":     "var cookieDomain  = \"booktracker.org\";"
        }

    @classmethod
    def get_options(cls):
        return cls._get_merged_options()

    # ===

    def is_torrent_changed(self, torrent):
        self._assert_match(torrent)
        page = _decode(self._read_url(torrent.get_comment()))
        return (torrent.get_mtime() < self._get_upload_time(page))

    def _get_upload_time(self, page):
        date_match = re.search(r"Зарегистрирован &nbsp;\s*\[ <span title=\"[\w\s]+\">"
                               r"(\d\d\d\d-\d\d-\d\d \d\d:\d\d)</span> ]", page)
        self._assert_logic(date_match is not None, "Upload date not found")
        date = date_match.group(1)
        upload_time = int(datetime.strptime(date, "%Y-%m-%d %H:%M").strftime("%s"))
        return upload_time

    def fetch_new_data(self, torrent):
        self._assert_match(torrent)
        page = _decode(self._read_url(torrent.get_comment()))

        dl_id_match = re.search(r"<a href=\"download\.php\?id=(\d+)\" class=\"\">", page)
        self._assert_logic(dl_id_match is not None, "Unknown dl_id")
        dl_id = dl_id_match.group(1)

        data = self._read_url("http://booktracker.org/download.php?id={}".format(dl_id))
        self._assert_valid_data(data)
        return data

    # ===

    def login(self):
        self._assert_auth(self._user is not None, "Required user for site")
        self._assert_auth(self._passwd is not None, "Required passwd for site")

        post_data = _encode(urllib.parse.urlencode({
            "login_username": _encode(self._user),
            "login_password": _encode(self._passwd),
            "login":          _encode("Вход"),
        }))
        page = _decode(self._read_url("http://booktracker.org/login.php", data=post_data))
        logout = "<b class=\"med\">{}</b></a>&nbsp; [ <a href=\"./login.php?logout=1".format(self._user)
        self._assert_auth(logout in page, "Invalid user or password")

        self._tzinfo = self._get_tzinfo()

    def _get_tzinfo(self):
        page = _decode(self._read_url("http://booktracker.org/profile.php?mode=editprofile"))
        timezone_match = re.search(r"<option value=\"[\.\d+-]\" selected=\"selected\">(GMT [+-] [\d\.]+)[\s<\(]", page)
        timezone = (timezone_match and "Etc/" + timezone_match.group(1).replace(" ", ""))
        return self._select_tzinfo(timezone)
