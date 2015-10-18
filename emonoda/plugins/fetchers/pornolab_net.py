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
from . import WithCaptcha
from . import WithTime


# =====
def _encode(arg):
    return arg.encode("cp1251")


def _decode(arg):
    return arg.decode("cp1251")


class Plugin(BaseFetcher, WithLogin, WithCaptcha, WithTime):
    def __init__(self, **kwargs):  # pylint: disable=super-init-not-called
        self._init_bases(**kwargs)
        self._init_opener(with_cookies=True)
        self._comment_regexp = re.compile(r"http://pornolab\.net/forum/viewtopic\.php\?t=(\d+)")
        self._tzinfo = None

    @classmethod
    def get_name(cls):
        return "pornolab.net"

    @classmethod
    def get_version(cls):
        return 1

    @classmethod
    def get_fingerprint(cls):
        return {
            "url":      "http://pornolab.net/forum/index.php",
            "encoding": "cp1251",
            "text":     "<link rel=\"search\" type=\"application/opensearchdescription+xml\" title=\"Поиск на Pornolab.net\""
                        " href=\"http://static.pornolab.net/opensearch.xml\">",
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
        date_match = re.search(r"<span title=\"Зарегистрирован\">\[ (\d\d-([а-яА-Я]{3})-\d\d \d\d:\d\d) \]</span>", page)
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

        upload_time = int(datetime.strptime(date, "%d-%m-%y %H:%M %z").strftime("%s"))
        return upload_time

    def fetch_new_data(self, torrent):
        self._assert_match(torrent)
        topic_id = self._comment_regexp.match(torrent.get_comment()).group(1)
        data = self._read_url("http://pornolab.net/forum/dl.php?t={}".format(topic_id), data=b"")
        self._assert_valid_data(data)
        return data

    # ===

    def login(self):
        self._assert_auth(self._user is not None, "Required user for site")
        self._assert_auth(self._passwd is not None, "Required passwd for site")

        post = {
            "login_username": _encode(self._user),
            "login_password": _encode(self._passwd),
            "login":          b"\xc2\xf5\xee\xe4",
        }
        page = self._read_login(post)

        cap_static_regexp = re.compile(r"\"(http://static\.pornolab\.net/captcha/[^\"]+)\"")
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

        self._tzinfo = self._get_tzinfo(page)

    def _read_login(self, post):
        return _decode(self._read_url(
            url="http://pornolab.net/forum/login.php",
            data=_encode(urllib.parse.urlencode(post)),
        ))

    def _get_tzinfo(self, page):
        timezone_match = re.search(r"<p>Часовой пояс: <span class='tz_time'>(GMT [+-] \d{1,2})</span></p>", page)
        timezone = (timezone_match and "Etc/" + timezone_match.group(1).replace(" ", ""))
        return self._select_tzinfo(timezone)
