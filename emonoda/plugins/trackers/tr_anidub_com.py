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
import operator

from datetime import datetime

from typing import Tuple
from typing import List
from typing import Dict
from typing import Any

from dateutil.relativedelta import relativedelta

from ...optconf import Option

from ...tfile import Torrent

from . import WithLogin
from . import WithCheckTime


# =====
class Plugin(WithLogin, WithCheckTime):
    PLUGIN_NAMES = ["tr.anidub.com"]

    _SITE_VERSION = 2

    _SITE_FINGERPRINT_URL = "https://tr.anidub.com"
    _SITE_FINGERPRINT_TEXT = ("<link rel=\"search\" type=\"application/opensearchdescription+xml\""
                              " href=\"https://tr.anidub.com/engine/opensearch.php\"")

    _COMMENT_REGEXP = re.compile(r"https?://tr\.anidub\.com/\?newsid=(?P<torrent_id>\d+)")

    _TIMEZONE_STATIC = "Etc/GMT+4"

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
            regexp=re.compile(r"<li><b>Дата:</b> ([^,\s]+, \d\d:\d\d)</li>"),
            text=self._decode(self._read_url("https://tr.anidub.com/?newsid={}".format(torrent_id))),
            msg="Upload date not found",
        ).group(1)

        now = datetime.now(self._tzinfo)
        day_template = "{date.day:02d}-{date.month:02d}-{date.year}"
        if "Сегодня" in date:
            date = date.replace("Сегодня", day_template.format(date=now))
        if "Вчера" in date:
            yesterday = now - relativedelta(days=1)
            date = date.replace("Вчера", day_template.format(date=yesterday))
        date += " " + datetime.now(self._tzinfo).strftime("%z")

        upload_time = int(datetime.strptime(date, "%d-%m-%Y, %H:%M %z").strftime("%s"))
        return upload_time

    def fetch_new_data(self, torrent: Torrent) -> bytes:
        torrent_id = self._assert_match(torrent)
        page = self._decode(self._read_url("https://tr.anidub.com/?newsid={}".format(torrent_id)))
        downloads = set(map(int, re.findall(r"<a href=\"/engine/download.php\?id=(\d+)\" class=\" \">", page)))
        candidates: Dict[str, List[Tuple[Torrent, str]]] = {}
        for download_id in downloads:
            data = self._assert_valid_data(self._read_url(
                url="https://tr.anidub.com/engine/download.php?id={}".format(download_id),
                headers={"Referer": "https://tr.anidub.com/?newsid={}".format(torrent_id)},
            ))
            candidate = Torrent(data=data)

            name = candidate.get_name()
            candidates.setdefault(name, [])
            candidates[name].append((candidate, str(download_id)))

        name = torrent.get_name()
        self._assert_logic(name in candidates, "Can't find torrent named '{}' in downloads".format(name))
        self._assert_logic(len(candidates[name]) == 1, "Too many variants to download: {}".format(
                                                       ", ".join(map(operator.itemgetter(1), candidates[name]))))
        return candidates[name][0][0].get_data()

    def login(self) -> None:
        self._login_using_post(
            url="https://tr.anidub.com/",
            post={
                "login_name":      self._encode(self._user),
                "login_password":  self._encode(self._passwd),
                "login":           b"submit",
            },
            ok_text="<li><a href=\"https://tr.anidub.com/user/{}/\">Мой профиль</a></li>".format(self._user)
        )
