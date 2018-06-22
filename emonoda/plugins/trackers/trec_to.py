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
from . import WithCaptcha
from . import WithCheckTime
from . import WithFetchByDownloadId
from . import WithStat


# =====
class Plugin(WithLogin, WithCaptcha, WithCheckTime, WithFetchByDownloadId, WithStat):
    PLUGIN_NAMES = [
        "trec.to",
        "torrent.rus.ec",
    ]

    _SITE_VERSION = 1
    _SITE_ENCODING = "utf-8"

    _SITE_FINGERPRINT_URL = "http://trec.to"
    _SITE_FINGERPRINT_TEXT = "var cookieDomain  = \"trec.to\";"

    _COMMENT_REGEXP = re.compile(r"http://(torrent\.rus\.ec|trec\.to)/viewtopic\.php\?p=(?P<torrent_id>\d+)")

    _TIMEZONE_URL = "http://trec.to"
    _TIMEZONE_REGEXP = re.compile(r"<p>Часовой пояс: <span class=\"tz_time\">(?P<timezone>GMT [+-] \d{1,2})</span></p>")
    _TIMEZONE_PREFIX = "Etc/"

    _DOWNLOAD_ID_URL = "http://trec.to/viewtopic.php?p={torrent_id}"
    _DOWNLOAD_ID_REGEXP = re.compile(r"<a href=\"download\.php\?id=(?P<download_id>\d+)\" class=\"(leech|seed|gen)med\">")
    _DOWNLOAD_URL = "http://trec.to/download.php?id={download_id}"

    _STAT_URL = _DOWNLOAD_ID_URL
    _STAT_OK_REGEXP = _DOWNLOAD_ID_REGEXP
    _STAT_SEEDERS_REGEXP = re.compile(r"<span class=\"seed\">Сидов:&nbsp;\s+<b>(?P<seeders>\d+)</b>")
    _STAT_LEECHERS_REGEXP = re.compile(r"<span class=\"leech\">Личеров:&nbsp;\s+<b>(?P<leechers>\d+)</b>")

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
            regexp=re.compile(r"<td width=\"70%\">\s*Зарегистрирован &nbsp;\s*\[ <span title=\"\">"
                              r"(\d\d-\d\d-\d\d\d\d \d\d:\d\d)</span> ]\s*</td>"),
            text=self._decode(self._read_url("http://trec.to/viewtopic.php?p={}".format(torrent_id))),
            msg="Upload date not found",
        ).group(1)
        date += " " + datetime.now(self._tzinfo).strftime("%z")
        upload_time = int(datetime.strptime(date, "%d-%m-%Y %H:%M %z").strftime("%s"))
        return upload_time

    def login(self) -> None:
        self._login_using_post(
            url="http://trec.to/login.php",
            post={
                "login_username": self._encode(self._user),
                "login_password": self._encode(self._passwd),
                "login":          self._encode("Вход"),
            },
            ok_text="<a href=\"./login.php?logout=1\" onclick=\"return confirm",
        )
