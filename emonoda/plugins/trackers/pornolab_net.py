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

from . import BaseTracker
from . import WithLogin
from . import WithCaptcha
from . import WithCheckTime
from . import WithFetchByTorrentId


# =====
class Plugin(BaseTracker, WithLogin, WithCaptcha, WithCheckTime, WithFetchByTorrentId):
    PLUGIN_NAME = "pornolab.net"

    _SITE_VERSION = 3
    _SITE_ENCODING = "cp1251"

    _SITE_FINGERPRINT_URL = "https://pornolab.net/forum/index.php"
    _SITE_FINGERPRINT_TEXT = "title=\"Поиск на Pornolab.net\" href=\"//static.pornolab.net/opensearch.xml\""

    _COMMENT_REGEXP = re.compile(r"https?://pornolab\.net/forum/viewtopic\.php\?t=(?P<torrent_id>\d+)")

    _TIMEZONE_URL = "https://pornolab.net/forum/index.php"
    _TIMEZONE_REGEXP = re.compile(r"<p>Часовой пояс: <span class='tz_time'>(?P<timezone>GMT [+-] \d{1,2})</span></p>")
    _TIMEZONE_PREFIX = "Etc/"

    _DOWNLOAD_URL = "https://pornolab.net/forum/dl.php?t={torrent_id}"
    _DOWNLOAD_PAYLOAD = b""

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
        date_match = re.search(r"<span title=\"Зарегистрирован\">\[ (\d\d-([а-яА-Я]{3})-\d\d \d\d:\d\d:\d\d) \]</span>", page)
        self._assert_logic(date_match is not None, "Upload date not found")
        date = date_match.group(1)
        date_month = date_match.group(2)

        date = date.replace(date_month, {
            month: str(number) for (number, month) in enumerate(
                ("Янв", "Фев", "Мар", "Апр", "Май", "Июн",
                 "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"), 1
            )
        }[date_month])  # TODO: Send shitbeam to datetime authors
        date += " " + datetime.now(self._tzinfo).strftime("%z")

        upload_time = int(datetime.strptime(date, "%d-%m-%y %H:%M:%S %z").strftime("%s"))
        return upload_time

    def login(self):
        self._assert_required_user_passwd()

        post = {
            "login_username": self._encode(self._user),
            "login_password": self._encode(self._passwd),
            "login":          b"\xc2\xf5\xee\xe4",
        }
        page = self._read_login(post)

        cap_static_regexp = re.compile(r"\"(https?://static\.pornolab\.net/captcha/[^\"]+)\"")
        cap_static_match = cap_static_regexp.search(page)
        if cap_static_match is not None:
            cap_sid_match = re.search(r"name=\"cap_sid\" value=\"([a-zA-Z0-9]+)\"", page)
            cap_code_match = re.search(r"name=\"(cap_code_[a-zA-Z0-9]+)\"", page)
            self._assert_auth(cap_sid_match is not None, "Unknown cap_sid")
            self._assert_auth(cap_code_match is not None, "Unknown cap_code")

            post[cap_code_match.group(1)] = self._captcha_decoder(cap_static_match.group(1))
            post["cap_sid"] = cap_sid_match.group(1)
            page = self._read_login(post)
            self._assert_auth(cap_static_regexp.search(page) is None, "Invalid user, password or captcha")

    def _read_login(self, post):
        return self._decode(self._read_url(
            url="https://pornolab.net/forum/login.php",
            data=self._encode(urllib.parse.urlencode(post)),
        ))
