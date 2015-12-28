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
from ... import tools

from . import BaseConfetti
from . import WithProxy


# =====
class Plugin(BaseConfetti, WithProxy):
    PLUGIN_NAME = "nma"

    def __init__(self, api_keys, **kwargs):  # pylint: disable=super-init-not-called
        self._init_bases(**kwargs)

        self._api_keys = api_keys

    @classmethod
    def get_options(cls):
        return cls._get_merged_options({
            "api_keys": Option(default=["CHANGE_ME"], type=as_string_list, help="API keys (or one key as string)"),
        })

    # ===

    def send_results(self, source, results):
        for result in results["affected"].values():
            self._notify(
                app="Emonoda ({})".format(source),
                event="{}".format(result["torrent"].get_name()),
                description=self._format_description(result["diff"]),
            )

    # ===

    def _format_description(self, diff):
        description_lines = []
        for (sign, items) in (
            ("+", diff["added"]),
            ("-", diff["removed"]),
            ("~", diff["modified"]),
            ("?", diff["type_modified"]),
        ):
            for item in tools.sorted_paths(items):
                description_lines.append("[{}] {}".format(sign, item))
        description = "Affected {} files\n".format(len(description_lines)) + "\n".join(description_lines)
        if len(description) > 9999:
            description = description[:9995] + "..."
        return description

    def _notify(self, app, event, description):
        # http://www.notifymyandroid.com/api.jsp
        post = {
            "apikey":       ",".join(self._api_keys),
            "application":  app,
            "event":        event,
            "description":  description,
            "Content-Type": "text/plain",
        }
        web.read_url(
            opener=web.build_opener(proxy_url=self._proxy_url),
            url="https://www.notifymyandroid.com/publicapi/notify",
            data=urllib.parse.urlencode(post).encode("utf-8"),
            timeout=self._timeout,
            retries=self._retries,
            retries_sleep=self._retries_sleep,
        )
