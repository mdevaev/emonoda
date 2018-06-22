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

from typing import Dict
from typing import Any

from ...optconf import Option

from . import WithLogin
from . import WithCheckHash
from . import WithFetchByDownloadId
from . import WithStat


# =====
class Plugin(WithLogin, WithCheckHash, WithFetchByDownloadId, WithStat):
    PLUGIN_NAMES = [
        "tfile.cc",
        "www1.tfiles.cc",
        "tfile-home.org",
        "tfile.co",
    ]

    _SITE_VERSION = 7
    _SITE_ENCODING = "cp1251"

    _SITE_FINGERPRINT_URL = "http://www1.tfiles.cc"
    _SITE_FINGERPRINT_TEXT = "href=\"http://www1.tfiles.cc/opensearch.xml\""

    _COMMENT_REGEXP = re.compile(r"http://((tfile\.(me|ru|co|cc))|tfile-home\.org|www1\.tfiles\.cc)"
                                 r"/forum/viewtopic\.php\?p=(?P<torrent_id>\d+)")

    _TORRENT_HASH_URL = "http://www1.tfiles.cc/forum/viewtopic.php?p={torrent_id}"
    _TORRENT_HASH_REGEXP = re.compile(r"<td style=\"color:darkgreen\">Info hash:</td>"
                                      r"<td><strong>(?P<torrent_hash>[a-fA-F0-9]{40})</strong></td>")

    _DOWNLOAD_ID_URL = "http://www1.tfiles.cc/forum/viewtopic.php?p={torrent_id}"
    _DOWNLOAD_ID_REGEXP = re.compile(r"<a href=\"download.php\?id=(?P<download_id>\d+)\""
                                     r" style=\"background:url\(/blueGene/images/topic\.jpg\)")
    _DOWNLOAD_URL = "http://www1.tfiles.cc/forum/download.php?id={download_id}"

    _STAT_URL = _TORRENT_HASH_URL
    _STAT_OK_REGEXP = _TORRENT_HASH_REGEXP
    _STAT_SEEDERS_REGEXP = re.compile(r"<span class=\"seed\" id=\"seedStats\"><b>(?P<seeders>\d+)</b>")
    _STAT_LEECHERS_REGEXP = re.compile(r"<span class=\"leech\" id=\"leechStats\"><b>(?P<leechers>\d+)</b>")

    # =====

    def __init__(self, **kwargs: Any) -> None:  # pylint: disable=super-init-not-called
        self._init_bases(**kwargs)
        self._init_opener(with_cookies=True)

    @classmethod
    def get_options(cls) -> Dict[str, Option]:
        return cls._get_merged_options()

    def login(self) -> None:
        self._login_using_post(
            url="http://www1.tfiles.cc/login/",
            post={
                "username":  self._encode(self._user),
                "password":  self._encode(self._passwd),
                "autologin": b"",
                "login":     b"",
            },
            ok_text="class=\"nick u\">{}</a>".format(self._user),
        )
