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
    PLUGIN_NAMES = [
        "nnm-club.me",
        "nnm-club.name",
        "nnmclub.to",
    ]

    _NNM_DOMAIN = PLUGIN_NAMES[0]

    _SITE_VERSION = 5
    _SITE_ENCODING = "cp1251"

    _SITE_FINGERPRINT_URL = "https://{}".format(_NNM_DOMAIN)
    _SITE_FINGERPRINT_TEXT = "<link rel=\"canonical\" href=\"http://{}/\">".format(_NNM_DOMAIN)

    _COMMENT_REGEXP = re.compile(r"https?://(nnm-club\.(me|ru|name|tv|lib)|nnmclub\.to)"
                                 r"/forum/viewtopic\.php\?p=(?P<torrent_id>\d+)")

    _TIMEZONE_URL = "https://{}/forum/profile.php?mode=editprofile".format(_NNM_DOMAIN)
    _TIMEZONE_REGEXP = re.compile(r"selected=\"selected\">(?P<timezone>GMT [+-] [\d:]+)")
    _TIMEZONE_PREFIX = "Etc/"

    _DOWNLOAD_ID_URL = "https://{}/forum/viewtopic.php?p={{torrent_id}}".format(_NNM_DOMAIN)
    _DOWNLOAD_ID_REGEXP = re.compile(r"filelst.php\?attach_id=(?P<download_id>[a-zA-Z0-9]+)")
    _DOWNLOAD_URL = "https://{}//forum/download.php?id={{download_id}}".format(_NNM_DOMAIN)

    _STAT_URL = _DOWNLOAD_ID_URL
    _STAT_OK_REGEXP = _DOWNLOAD_ID_REGEXP
    _STAT_SEEDERS_REGEXP = re.compile(r"align=\"center\"><span class=\"seed\">\[\s+<b>(?P<seeders>\d+)")
    _STAT_LEECHERS_REGEXP = re.compile(r"align=\"center\"><span class=\"leech\">\[\s+<b>(?P<leechers>\d+)")

    # =====

    def __init__(self, **kwargs: Any) -> None:  # pylint: disable=super-init-not-called
        self._init_bases(**kwargs)
        self._init_opener(with_cookies=True)

    @classmethod
    def get_options(cls) -> Dict[str, Option]:
        return cls._get_merged_options({
            "timeout": Option(default=20.0, help="Timeout for HTTP client"),
        })

    def fetch_time(self, torrent: Torrent) -> int:
        torrent_id = self._assert_match(torrent)
        date = self._assert_logic_re_search(
            regexp=re.compile(r"<td class=\"genmed\">&nbsp;Зарегистрирован:&nbsp;</td>"
                              r"\s*<td class=\"genmed\">&nbsp;(\d{1,2} ... \d{4} \d\d:\d\d:\d\d)</td>"),
            text=self._decode(self._read_url("https://{}/forum/viewtopic.php?p={}".format(self._NNM_DOMAIN, torrent_id))),
            msg="Upload date not found",
        ).group(1).lower()
        for (m_src, m_dest) in [
            ("янв", "01"),
            ("фев", "02"),
            ("мар", "03"),
            ("апр", "04"),
            ("май", "05"),
            ("июн", "06"),
            ("июл", "07"),
            ("авг", "08"),
            ("сен", "09"),
            ("окт", "10"),
            ("ноя", "11"),
            ("дек", "12"),
        ]:
            date = date.replace(m_src, m_dest)
        date += " " + datetime.now(self._tzinfo).strftime("%z")
        upload_time = int(datetime.strptime(date, "%d %m %Y %H:%M:%S %z").strftime("%s"))
        return upload_time

    def login(self) -> None:
        self._login_using_post(
            url="https://{}/forum/login.php".format(self._NNM_DOMAIN),
            post={
                "username": self._encode(self._user),
                "password": self._encode(self._passwd),
                "redirect": b"",
                "login":    b"\xc2\xf5\xee\xe4",
            },
            ok_text="class=\"mainmenu\">Выход [ {} ]</a>".format(self._user),
        )
