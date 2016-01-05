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
from . import WithFetchByTorrentId


# =====
class Plugin(BaseTracker, WithLogin, WithCheckTime, WithFetchByTorrentId):
    PLUGIN_NAME = "kinozal.tv"

    _SITE_VERSION = 0
    _SITE_ENCODING = "cp1251"

    _SITE_FINGERPRINT_URL = "http://kinozal.tv/"
    _SITE_FINGERPRINT_TEXT = "<title>Торрент трекер Кинозал.ТВ</title>"

    _COMMENT_REGEXP = re.compile(r"http://kinozal\.tv/details\.php\?id=(?P<torrent_id>\d+)")

    _TIMEZONE_URL = "http://kinozal.tv/my.php"
    _TIMEZONE_REGEXP = re.compile(r"<option value=\"(?P<delta>-?\d{1,3})\" selected")
    _TIMEZONE_PREFIX = "Etc/GMT"

    _DOWNLOAD_URL = "http://dl.kinozal.tv/download.php?id={torrent_id}"
    _DOWNLOAD_PAYLOAD = b""

    # ===

    def __init__(self, **kwargs):  # pylint: disable=super-init-not-called
        self._init_bases(**kwargs)
        self._init_opener(with_cookies=True)

    @classmethod
    def get_options(cls):
        return cls._get_merged_options()

    def init_tzinfo(self):
        timezone = None
        page = self._decode(self._read_url(self._TIMEZONE_URL))
        delta_match = self._TIMEZONE_REGEXP.search(page)
        if delta_match:
            timezone_gmt_number = (int(delta_match.group("delta")) + 180) // 60  # Moscow Timezone GMT+3 -> 3 * 60 = 180
            if timezone_gmt_number > 0:
                timezone = self._TIMEZONE_PREFIX + "+" + str(timezone_gmt_number)
            else:
                timezone = self._TIMEZONE_PREFIX + str(timezone_gmt_number)
        self._tzinfo = self._select_tzinfo(timezone)

    def fetch_time(self, torrent):
        self._assert_match(torrent)
        page = self._decode(self._read_url(torrent.get_comment()))

        for label in ("Обновлен", "Залит"):
            date_match = re.search(r"<li>%s<span class=\"floatright green n\">"
                                   r"(\d{1,2}) ([А-Яа-я]{3,8}) (\d{4}) в (\d{2}:\d{2})"
                                   r"</span></li>" % (label), page)
            if date_match is not None:
                break
        self._assert_logic(date_match is not None, "Upload date not found")

        months = {
            "января":   "01",
            "февраля":  "02",
            "марта":    "03",
            "апреля":   "04",
            "мая":      "05",
            "июня":     "06",
            "июля":     "07",
            "августа":  "08",
            "сентября": "09",
            "октября":  "10",
            "ноября":   "11",
            "декабря":  "12",
        }
        date_str = "%s %s %s %s %s" % (
            date_match.group(1),  # Day
            months[date_match.group(2)],  # Month
            date_match.group(3),  # Year
            date_match.group(4),  # Time
            datetime.now(self._tzinfo).strftime("%z")  # Timezone offset
        )
        upload_time = int(datetime.strptime(date_str, "%d %m %Y %H:%M %z").strftime("%s"))
        return upload_time

    def login(self):
        self._login_using_post(
            url="http://kinozal.tv/takelogin.php",
            post={
                "username": self._encode(self._user),
                "password": self._encode(self._passwd),
                "returnto": "",
            },
            ok_text="href=\"/my.php\"",
        )
