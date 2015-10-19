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

from . import nnm_club_me


# =====
class Plugin(nnm_club_me.Plugin):
    _domain = "ipv6.nnm-club.me"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._comment_regexp = re.compile(r"http://ipv6\.nnm-club\.(me|ru)/forum/viewtopic\.php\?p=(\d+)")

    @classmethod
    def get_name(cls):
        return "ipv6.nnm-club.me"

    @classmethod
    def get_version(cls):
        return 0
