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
from . import WithFetchByTorrentId
from . import WithStat


# =====
class Plugin(WithLogin, WithCaptcha, WithCheckTime, WithFetchByTorrentId, WithStat):
    PLUGIN_NAMES = ["pornolab.net"]

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

    _STAT_URL = "https://pornolab.net/forum/viewtopic.php?t={torrent_id}"
    _STAT_OK_REGEXP = re.compile(r"class=\"dl-stub dl-link\">Скачать \.torrent</a></p>")
    _STAT_SEEDERS_REGEXP = re.compile(r"<span class=\"seed\">Сиды:&nbsp;\s+<b>(?P<seeders>\d+)</b>")
    _STAT_LEECHERS_REGEXP = re.compile(r"<span class=\"leech\">Личи:&nbsp;\s+<b>(?P<leechers>\d+)</b>")

    # =====

    def __init__(self, **kwargs: Any) -> None:  # pylint: disable=super-init-not-called
        self._init_bases(**kwargs)
        self._init_opener(with_cookies=True)

    @classmethod
    def get_options(cls) -> Dict[str, Option]:
        return cls._get_merged_options()

    def fetch_time(self, torrent: Torrent) -> int:
        torrent_id = self._assert_match(torrent)

        date_match = self._assert_logic_re_search(
            regexp=re.compile(r"<span title=\"Зарегистрирован\">\[ (\d\d-([а-яА-Я]{3})-\d\d \d\d:\d\d:\d\d) \]</span>"),
            text=self._decode(self._read_url("https://pornolab.net/forum/viewtopic.php?t={}".format(torrent_id))),
            msg="Upload date not found",
        )
        date = date_match.group(1)
        date_month = date_match.group(2)

        date = date.replace(date_month, {
            month: str(number) for (number, month) in enumerate(
                ["Янв", "Фев", "Мар", "Апр", "Май", "Июн",
                 "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"], 1
            )
        }[date_month])  # Send shitbeam to datetime authors
        date += " " + datetime.now(self._tzinfo).strftime("%z")

        upload_time = int(datetime.strptime(date, "%d-%m-%y %H:%M:%S %z").strftime("%s"))
        return upload_time

    def login(self) -> None:
        self._assert_required_user_passwd()

        post = {
            "login_username": self._encode(self._user),
            "login_password": self._encode(self._passwd),
            "login":          b"\xc2\xf5\xee\xe4",
        }
        page = self.__read_login(post)

        cap_static_regexp = re.compile(r"\"(https?://static\.pornolab\.net/captcha/[^\"]+)\"")
        cap_static_match = cap_static_regexp.search(page)
        if cap_static_match is not None:
            cap_sid = self._assert_auth_re_search(
                regexp=re.compile(r"name=\"cap_sid\" value=\"([a-zA-Z0-9]+)\""),
                text=page,
                msg="Unknown cap_sid",
            ).group(1)

            cap_code = self._assert_auth_re_search(
                regexp=re.compile(r"name=\"(cap_code_[a-zA-Z0-9]+)\""),
                text=page,
                msg="Unknown cap_code",
            ).group(1)

            post[cap_code] = self._encode(self._captcha_decoder(cap_static_match.group(1)))
            post["cap_sid"] = self._encode(cap_sid)

            page = self.__read_login(post)
            self._assert_auth(cap_static_regexp.search(page) is None, "Invalid user, password or captcha")

    def __read_login(self, post: Dict[str, bytes]) -> str:
        return self._decode(self._read_url(
            url="https://pornolab.net/forum/login.php",
            data=self._urlencode(post),
        ))
