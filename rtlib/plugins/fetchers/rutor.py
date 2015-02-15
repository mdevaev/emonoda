"""
    rtfetch -- The set of tools to organize and manage your torrents
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

from . import BaseFetcher
from . import WithOpener
from . import build_opener


# =====
def _decode(arg):
    return arg.decode("utf-8")


class Plugin(BaseFetcher, WithOpener):
    def __init__(self, **kwargs):  # pylint: disable=super-init-not-called
        for parent in self.__class__.__bases__:
            parent.__init__(self, **kwargs)

        self._comment_regexp = re.compile(r"^http://rutor\.org/torrent/(\d+)$")
        self._hash_regexp = re.compile(r"<div id=\"download\">\s+<a href=\"magnet:\?xt=urn:btih:([a-fA-F0-9]{40})")

    @classmethod
    def get_name(cls):
        return "rutor.org"

    @classmethod
    def get_version(cls):
        return 1

    @classmethod
    def get_options(cls):
        params = {}
        for parent in cls.__bases__:
            params.update(parent.get_options())
        params["user_agent"] = Option(default="Googlebot/2.1", help="User-agent for site")
        return params

    def test_site(self):
        opener = build_opener(proxy_url=self._proxy_url)
        data = self._read_url("http://rutor.org", opener=opener)
        self._assert_site(b"<link rel=\"shortcut icon\" href=\"http://s.rutor.org/favicon.ico\" />" in data)

    def is_matched_for(self, torrent):
        return (self._comment_regexp.match(torrent.get_comment() or "") is not None)

    def is_torrent_changed(self, torrent):
        self._assert_match(torrent)
        return (torrent.get_hash() != self._fetch_hash(torrent))

    def fetch_new_data(self, torrent):
        self._assert_match(torrent)
        comment_match = self._comment_regexp.match(torrent.get_comment() or "")
        topic_id = comment_match.group(1)
        data = self._read_url("http://d.rutor.org/download/{}".format(topic_id))
        self._assert_valid_data(data)
        return data

    # ===

    def _fetch_hash(self, torrent):
        text = _decode(self._read_url(torrent.get_comment()))
        hash_match = self._hash_regexp.search(text)
        self._assert_logic(hash_match is not None, "Hash not found")
        return hash_match.group(1).lower()
