#####
#
#    rtfetch -- Update rtorrent files from popular trackers
#    Copyright (C) 2012  Devaev Maxim <mdevaev@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#####


import urllib.parse
import re

from ...core import tfile

from . import BaseFetcher
from . import WithLogin
from . import WithOpener
from . import build_opener


# =====
def _encode(arg):
    return arg.encode("cp1251")


def _decode(arg):
    return arg.decode("cp1251")


class Plugin(BaseFetcher, WithLogin, WithOpener):
    def __init__(self, **kwargs):  # pylint: disable=super-init-not-called
        for parent in self.__class__.__bases__:
            parent.__init__(self, **kwargs)

        self._comment_regexp = re.compile(r"http://nnm-club\.(me|ru)/forum/viewtopic\.php\?p=(\d+)")
        self._torrent_id_regexp = re.compile(r"filelst.php\?attach_id=([a-zA-Z0-9]+)")

    @classmethod
    def get_name(cls):
        return "nnmclub"

    @classmethod
    def get_version(cls):
        return 1

    @classmethod
    def get_options(cls):
        params = {}
        for parent in cls.__bases__:
            params.update(parent.get_options())
        return params

    def test_site(self):
        opener = build_opener(proxy_url=self._proxy_url)
        data = self._read_url("http://nnm-club.me", opener=opener)
        self._assert_site(b"<link rel=\"canonical\" href=\"http://nnm-club.me/\">" in data)

    def is_matched_for(self, torrent):
        return (self._comment_regexp.match(torrent.get_comment() or "") is not None)

    def is_torrent_changed(self, torrent):
        self._assert_match(torrent)
        url = "http://bt.nnm-club.me:2710/scrape?info_hash={}".format(torrent.get_scrape_hash())
        headers = {"User-Agent": self._client_agent}
        data = self._read_url(url, headers=headers)
        return (len(tfile.decode_data(data).get("files", {})) == 0)

    def fetch_new_data(self, torrent):
        self._assert_match(torrent)
        data = _decode(self._read_url(torrent.get_comment().replace("nnm-club.ru", "nnm-club.me")))

        torrent_id_match = self._torrent_id_regexp.search(data)
        self._assert_logic(torrent_id_match is not None, "Unknown torrent_id")
        torrent_id = torrent_id_match.group(1)

        data = self._read_url("http://nnm-club.me//forum/download.php?id={}".format(torrent_id))
        self._assert_valid_data(data)
        return data

    # ===

    def login(self):
        self._assert_auth(self._user is not None, "Required user nnmclub")
        self._assert_auth(self._passwd is not None, "Required passwd nnmclub")
        with self._make_opener():
            post = {
                "username": _encode(self._user),
                "password": _encode(self._passwd),
                "redirect": b"",
                "login":    b"\xc2\xf5\xee\xe4",
            }
            url = "http://nnm-club.me/forum/login.php"
            data = _encode(urllib.parse.urlencode(post))
            text = _decode(self._read_url(url, data=data))
            self._assert_auth("[ {} ]".format(self._user) in text, "Invalid login")

    def is_logged_in(self):
        return (self._opener is not None)
