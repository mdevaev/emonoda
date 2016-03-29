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

from . import nnmclub_to


# =====
class Plugin(nnmclub_to.Plugin):
    PLUGIN_NAME = _NNM_DOMAIN = "ipv6.nnmclub.to"

    _SITE_VERSION = 0
    _SITE_FINGERPRINT_URL = "http://{}".format(_NNM_DOMAIN)

    _COMMENT_REGEXP = re.compile(r"http://ipv6\.(nnm-club\.(me|ru)|nnmclub\.to)/forum/viewtopic\.php\?p=(?P<torrent_id>\d+)")

    _TORRENT_SCRAPE_URL = "http://bt.{}:2710/scrape.php?info_hash={{scrape_hash}}".format(_NNM_DOMAIN)

    _DOWNLOAD_ID_URL = "http://{}/forum/viewtopic.php?p={{torrent_id}}".format(_NNM_DOMAIN)
    _DOWNLOAD_URL = "http://{}//forum/download.php?id={{download_id}}".format(_NNM_DOMAIN)
