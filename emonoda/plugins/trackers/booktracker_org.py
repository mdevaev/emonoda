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

from datetime import datetime

from . import BaseTracker
from . import WithLogin
from . import WithCheckTime
from . import WithFetchByDownloadId


# =====
class Plugin(BaseTracker, WithLogin, WithCheckTime, WithFetchByDownloadId):
    PLUGIN_NAME = "booktracker.org"

    _SITE_VERSION = 1
    _SITE_ENCODING = "utf-8"

    _SITE_FINGERPRINT_URL = "https://booktracker.org"
    _SITE_FINGERPRINT_TEXT = "<meta name='yandex-verification' content='57e66f92f305434b' />"

    _COMMENT_REGEXP = re.compile(r"https?://booktracker\.org/viewtopic\.php\?p=(?P<torrent_id>\d+)")

    _TIMEZONE_URL = "https://booktracker.org/profile.php?mode=editprofile"
    _TIMEZONE_REGEXP = re.compile(r"<option value=\"[\.\d+-]\" selected=\"selected\">(?P<timezone>GMT [+-] [\d\.]+)[\s<\(]")
    _TIMEZONE_PREFIX = "Etc/"

    _DOWNLOAD_ID_URL = "https://booktracker.org/viewtopic.php?p={torrent_id}"
    _DOWNLOAD_ID_REGEXP = re.compile(r"<a href=\"download\.php\?id=(?P<download_id>\d+)\" class=\"\">")
    _DOWNLOAD_URL = "https://booktracker.org/download.php?id={download_id}"

    # ===

    def __init__(self, **kwargs):  # pylint: disable=super-init-not-called
        self._init_bases(**kwargs)
        self._init_opener(with_cookies=True)

    @classmethod
    def get_options(cls):
        return cls._get_merged_options()

    def fetch_time(self, torrent):
        self._assert_match(torrent)
        page = self._decode(self._read_url(torrent.get_comment()))

        date_match = re.search(r"Зарегистрирован &nbsp;\s*\[ <span title=\"[\w\s]+\">"
                               r"(\d\d\d\d-\d\d-\d\d \d\d:\d\d)</span> ]", page)
        self._assert_logic(date_match is not None, "Upload date not found")
        date = date_match.group(1)
        date += " " + datetime.now(self._tzinfo).strftime("%z")
        upload_time = int(datetime.strptime(date, "%Y-%m-%d %H:%M %z").strftime("%s"))
        return upload_time

    def login(self):
        self._login_using_post(
            url="https://booktracker.org/login.php",
            post={
                "login_username": self._encode(self._user),
                "login_password": self._encode(self._passwd),
                "login":          self._encode("Вход"),
            },
            ok_text="<b class=\"med\">{}</b></a>&nbsp; [ <a href=\"./login.php?logout=1".format(self._user),
        )
