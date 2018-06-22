"""
    Emonoda -- A set of tools to organize and manage your torrents
    Copyright (C) 2018  Devaev Maxim <mdevaev@gmail.com>

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
import json

from typing import Tuple
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
    PLUGIN_NAMES = ["telegram"]

    _SITE_RETRY_CODES = [429, 500, 502, 503]

    def __init__(  # pylint: disable=super-init-not-called
        self,
        token: str,
        chats: List[str],
        template: str,
        **kwargs: Any,
    ) -> None:

        self._init_bases(**kwargs)
        self._init_opener()

        self.__token = token
        self.__chats = chats
        self.__template_path = template

    @classmethod
    def get_options(cls) -> Dict[str, Option]:
        return cls._get_merged_options({
            "token":    SecretOption(default="CHANGE_ME", help="Bot token"),
            "chats":    SecretOption(default=[], type=as_string_list, help="Chats ids"),
            "template": Option(default="", type=as_path_or_empty, help="Mako template file name"),
        })

    def send_results(self, source: str, results: ResultsType) -> None:
        messages = [
            templated(
                name=(self.__template_path if self.__template_path else "telegram.{source}.mako").format(source=source),
                built_in=(not self.__template_path),
                source=source,
                file_name=file_name,
                status=status,
                status_msg=STATUSES[status],
                result=result,
            )
            for status in self._statuses
            for (file_name, result) in results[status].items()
        ]
        for chat_id in self.__chats:
            for msg in messages:
                self._read_url(
                    url="https://api.telegram.org/bot{}/sendMessage".format(self.__token),
                    data=urllib.parse.urlencode({
                        "chat_id": chat_id,
                        "text": msg,
                        "parse_mode": "html",
                        "disable_web_page_preview": True,
                    }).encode("utf-8"),
                )

    def get_last_chats(self, limit: int) -> List[Tuple[str, str]]:  # XXX: Only for emonoda.apps.emconfetti_tghi
        last_chats: List[Tuple[str, str]] = []
        for update in json.loads(self._read_url(
            url="https://api.telegram.org/bot{}/getUpdates?limit={}".format(self.__token, limit),
        ).decode("utf-8"))["result"]:
            if "edited_message" in update:
                update["message"] = update["edited_message"]
            if "text" in update["message"]:  # Only text messages
                user = update["message"]["from"].get("username", "")
                chat_id = str(update["message"]["chat"]["id"])
            last_chats.append((user, chat_id))
        return last_chats
