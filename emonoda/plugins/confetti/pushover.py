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

from ...optconf import Option
from ...optconf.converters import as_string_list

from ... import web

from . import BaseConfetti
from . import WithProxy


# =====
class Plugin(BaseConfetti, WithProxy):
    PLUGIN_NAME = "pushover"

    def __init__(self, user_key, api_key, devices, **kwargs):  # pylint: disable=super-init-not-called
        self._init_bases(**kwargs)

        self._user_key = user_key
        self._api_key = api_key
        self._devices = devices

    @classmethod
    def get_options(cls):
        return cls._get_merged_options({
            "user_key": Option(default="CHANGE_ME", type=str, help="User key"),
            "api_key":  Option(default="CHANGE_ME", type=str, help="API/Application key"),
            "devices":  Option(default=[], type=as_string_list, help="Devices list (empty for all)"),
        })

    # ===

    def send_results(self, source, results):
        for result in results["affected"].values():
            self._notify(
                title="Emonoda ({})".format(source),
                message=result["torrent"].get_name(),
            )

    # ===

    def _notify(self, title, message):
        # https://pushover.net/api
        post = {
            "token":   self._api_key,
            "user":    self._user_key,
            "title":   title,
            "message": message,
        }
        web.read_url(
            opener=web.build_opener(proxy_url=self._proxy_url),
            url="https://api.pushover.net/1/messages.json",
            data=urllib.parse.urlencode(post).encode("utf-8"),
            timeout=self._timeout,
            retries=self._retries,
            retries_sleep=self._retries_sleep,
        )
