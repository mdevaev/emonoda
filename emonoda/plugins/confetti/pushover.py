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

from typing import List
from typing import Dict
from typing import Any

from ...optconf import Option
from ...optconf.converters import as_string_list

from . import ResultsType
from . import WithWeb


# =====
class Plugin(WithWeb):
    PLUGIN_NAME = "pushover"

    def __init__(  # pylint: disable=super-init-not-called
        self,
        user_key: str,
        api_key: str,
        devices: List[str],
        **kwargs: Any,
    ) -> None:

        self._init_bases(**kwargs)
        self._init_opener()

        self.__user_key = user_key
        self.__api_key = api_key
        self.__devices = devices

    @classmethod
    def get_options(cls) -> Dict[str, Option]:
        return cls._get_merged_options({
            "user_key": Option(default="CHANGE_ME", help="User key"),
            "api_key":  Option(default="CHANGE_ME", help="API/Application key"),
            "devices":  Option(default=[], type=as_string_list, help="Devices list (empty for all)"),
        })

    # ===

    def send_results(self, source: str, results: ResultsType) -> None:
        for result in results["affected"].values():
            self._read_url(
                url="https://api.pushover.net/1/messages.json",
                data=urllib.parse.urlencode({
                    "token":   self.__api_key,
                    "user":    self.__user_key,
                    "title":   "Emonoda ({})".format(source),
                    "message": result.torrent.get_name(),  # type: ignore
                }).encode("utf-8"),
            )
