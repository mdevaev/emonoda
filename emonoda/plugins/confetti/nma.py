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

from ...tfile import TorrentsDiff

from ... import tools

from . import ResultsType
from . import WithWeb


# =====
class Plugin(WithWeb):
    PLUGIN_NAME = "nma"

    def __init__(  # pylint: disable=super-init-not-called
        self,
        api_keys: List[str],
        **kwargs: Any,
    ) -> None:

        self._init_bases(**kwargs)
        self._init_opener()

        self.__api_keys = api_keys

    @classmethod
    def get_options(cls) -> Dict[str, Option]:
        return cls._get_merged_options({
            "api_keys": Option(default=["CHANGE_ME"], type=as_string_list, help="API keys (or one key as string)"),
        })

    # ===

    def send_results(self, source: str, results: ResultsType) -> None:
        for result in results["affected"].values():
            self._read_url(
                url="https://www.notifymyandroid.com/publicapi/notify",
                data=urllib.parse.urlencode({
                    "apikey":       ",".join(self.__api_keys),
                    "application":  "Emonoda ({})".format(source),
                    "event":        "{}".format(result.torrent.get_name()),  # type: ignore
                    "description":  self.__format_description(result.diff),
                    "Content-Type": "text/plain",
                }).encode("utf-8"),
            )

    # ===

    def __format_description(self, diff: TorrentsDiff) -> str:
        description_lines = []
        for (sign, items) in [
            ("+", diff.added),
            ("-", diff.removed),
            ("~", diff.modified),
            ("?", diff.type_modified),
        ]:
            for item in tools.sorted_paths(items):
                description_lines.append("[{}] {}".format(sign, item))
        description = "Affected {} files\n".format(len(description_lines)) + "\n".join(description_lines)
        if len(description) > 9999:
            description = description[:9995] + "..."
        return description
