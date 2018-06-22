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
from ...optconf import SecretOption
from ...optconf.converters import as_string_list
from ...optconf.converters import as_path_or_empty

from . import STATUSES
from . import ResultsType
from . import WithWeb
from . import WithStatuses
from . import templated


# =====
class Plugin(WithWeb, WithStatuses):
    PLUGIN_NAMES = ["pushover"]

    def __init__(  # pylint: disable=super-init-not-called
        self,
        user_key: str,
        api_key: str,
        devices: List[str],
        title: str,
        template: str,
        **kwargs: Any,
    ) -> None:

        self._init_bases(**kwargs)
        self._init_opener()

        self.__user_key = user_key
        self.__api_key = api_key
        self.__devices = devices
        self.__title = title
        self.__template_path = template

    @classmethod
    def get_options(cls) -> Dict[str, Option]:
        return cls._get_merged_options({
            "user_key": SecretOption(default="CHANGE_ME", help="User key"),
            "api_key":  SecretOption(default="CHANGE_ME", help="API/Application key"),
            "devices":  Option(default=[], type=as_string_list, help="Devices list (empty for all)"),
            "title":    Option(default="Emonoda ({source})", help="Message title"),
            "template": Option(default="", type=as_path_or_empty, help="Mako template file name"),
        })

    def send_results(self, source: str, results: ResultsType) -> None:
        for status in self._statuses:
            for (file_name, result) in results[status].items():
                post = {
                    "token":   self.__api_key,
                    "user":    self.__user_key,
                    "html":    "1",
                    "title":   self.__title.format(source=source),
                    "message": templated(
                        name=(self.__template_path if self.__template_path else "pushover.{source}.mako").format(source=source),
                        built_in=(not self.__template_path),
                        source=source,
                        file_name=file_name,
                        status=status,
                        status_msg=STATUSES[status],
                        result=result,
                    ),
                }
                if self.__devices:
                    post["device"] = ",".join(self.__devices)
                self._read_url(
                    url="https://api.pushover.net/1/messages.json",
                    data=urllib.parse.urlencode(post).encode("utf-8"),
                )
