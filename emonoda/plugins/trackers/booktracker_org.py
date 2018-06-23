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

from typing import Dict
from typing import Any

from ...optconf import Option

from ...tfile import Torrent

from . import WithLogin
from . import WithCheckTime
from . import WithFetchByDownloadId
from . import WithStat


# =====
class Plugin(WithLogin, WithCheckTime, WithFetchByDownloadId, WithStat):
    PLUGIN_NAMES = ["booktracker.org"]

    _SITE_VERSION = 2

    _SITE_FINGERPRINT_URL = "https://booktracker.org"
    _SITE_FINGERPRINT_TEXT = "<meta name=\"google-site-verification\" content=\"L85kL3qg3y9JS1ER3BNhcpcqdDZBgrxzZpBm6Jzb1iQ\" />"

    _COMMENT_REGEXP = re.compile(r"https?://booktracker\.org(:443)?/viewtopic\.php\?p=(?P<torrent_id>\d+)")

    _TIMEZONE_URL = "https://booktracker.org/profile.php?mode=editprofile"
    _TIMEZONE_REGEXP = re.compile(r"<option value=\"[\.\d+-]\" selected=\"selected\">(?P<timezone>GMT [+-] [\d\.]+)[\s<\(]")
    _TIMEZONE_PREFIX = "Etc/"

    _DOWNLOAD_ID_URL = "https://booktracker.org/viewtopic.php?p={torrent_id}"
    _DOWNLOAD_ID_REGEXP = re.compile(r"<a href=\"download\.php\?id=(?P<download_id>\d+)\" class=\"\">")
    _DOWNLOAD_URL = "https://booktracker.org/download.php?id={download_id}"

    _STAT_URL = _DOWNLOAD_ID_URL
    _STAT_OK_REGEXP = _DOWNLOAD_ID_REGEXP
    _STAT_SEEDERS_REGEXP = re.compile(r"<b>Раздают:\s+(?P<seeders>\d+)</b></span> &#0183;")
    _STAT_LEECHERS_REGEXP = re.compile(r"<span class=\"leechmed\" ><b>Качают:\s+(?P<leechers>\d+)</b></span>")

    # =====

    def __init__(self, **kwargs: Any) -> None:  # pylint: disable=super-init-not-called
        self._init_bases(**kwargs)
        self._init_opener(with_cookies=True)

    @classmethod
    def get_options(cls) -> Dict[str, Option]:
        return cls._get_merged_options()

    def fetch_time(self, torrent: Torrent) -> int:
        torrent_id = self._assert_match(torrent)
        date = self._assert_logic_re_search(
            regexp=re.compile(r"Зарегистрирован &nbsp;\s*\[ <span title=\"[\w\s]+\">"
                              r"(\d\d\d\d-\d\d-\d\d \d\d:\d\d)</span> ]"),
            text=self._decode(self._read_url("https://booktracker.org/viewtopic.php?p={}".format(torrent_id))),
            msg="Upload date not found",
        ).group(1)
        date += " " + datetime.now(self._tzinfo).strftime("%z")
        upload_time = int(datetime.strptime(date, "%Y-%m-%d %H:%M %z").strftime("%s"))
        return upload_time

    def login(self) -> None:
        self._login_using_post(
            url="https://booktracker.org/login.php",
            post={
                "login_username": self._encode(self._user),
                "login_password": self._encode(self._passwd),
                "login":          self._encode("Вход"),
            },
            ok_text="<b class=\"med\">{}</b></a>&nbsp; [ <a href=\"./login.php?logout=1".format(self._user),
        )
