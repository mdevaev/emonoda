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

from ...optconf import Option

from . import BaseTracker
from . import WithCheckHash
from . import WithFetchByTorrentId


# =====
class Plugin(BaseTracker, WithCheckHash, WithFetchByTorrentId):
    PLUGIN_NAME = "rutor.info"

    _SITE_VERSION = 5
    _SITE_ENCODING = "utf-8"

    _SITE_FINGERPRINT_URL = "http://rutor.info"
    _SITE_FINGERPRINT_TEXT = "<a href=\"/\"><img src=\"http://s.rutor.info/logo.jpg\" alt=\"rutor.info logo\" /></a>"

    _COMMENT_REGEXP = re.compile(r"^http://rutor\.(info|org|is)/torrent/(?P<torrent_id>\d+)$")

    _TORRENT_HASH_URL = "http://rutor.info/torrent/{torrent_id}"
    _TORRENT_HASH_REGEXP = re.compile(r"<div id=\"download\">\s+<a href=\"magnet:"
                                      r"\?xt=urn:btih:(?P<torrent_hash>[a-fA-F0-9]{40})")

    _DOWNLOAD_URL = "http://rutor.info/download/{torrent_id}"

    # ===

    def __init__(self, **kwargs):  # pylint: disable=super-init-not-called
        self._init_bases(**kwargs)
        self._init_opener(with_cookies=False)

    @classmethod
    def get_options(cls):
        return cls._get_merged_options({
            "user_agent": Option(default="Googlebot/2.1", help="User-agent for site"),
        })
