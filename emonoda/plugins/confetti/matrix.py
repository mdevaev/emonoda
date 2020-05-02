"""
    Emonoda -- A set of tools to organize and manage your torrents
    Copyright (C) 2015  Devaev Maxim <mdevaev@gmail.com>

    atom.py -- produce atom feed file of recent torrent updates
    Copyright (C) 2017  Pavel Pletenev <cpp.create@gmail.com>

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


import os
import traceback
import time
import re

from typing import List
from typing import Dict
from typing import Any

import yaml

from ...optconf import Option
from ...optconf import SecretOption
from ...optconf.converters import as_string_list
from ...optconf.converters import as_path_or_empty


from . import ResultsType
from . import WithStatuses
from . import templated
from . import STATUSES

# =====
class Plugin(WithStatuses):  # pylint: disable=too-many-instance-attributes
    PLUGIN_NAMES = ["matrix"]

    def __init__(  # pylint: disable=super-init-not-called,too-many-arguments
        self,
        homeserver_url: str,
        username: str,
        password: str,
        room_ids: List[str],
        template: str,
        **kwargs: Any,
    ) -> None:

        self._init_bases(**kwargs)

        self.__homeserver_url = homeserver_url
        self.__username = username
        self.__password = password
        self.__room_ids = room_ids
        self.__template_path = template

    @classmethod
    def get_options(cls) -> Dict[str, Option]:
        return cls._get_merged_options({
            "homeserver_url": SecretOption(default="https://matrix.org", help="Matrix homeserver url"),
            "username":       SecretOption(default="CHANGE_ME",  help="Username in form of @name:example.com"),
            "password":       SecretOption(default="CHANGE_ME",  help="Password"),
            "room_ids":       SecretOption(default=[], type=as_string_list,  help="Room ids"),
            "template":       Option(default="", type=as_path_or_empty, help="Mako template file name")
        })

    def send_results(self, source: str, results: ResultsType) -> None:
        messages = [
            templated(
                name=(self.__template_path if self.__template_path else "matrix.{source}.mako").format(source=source),
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
        import asyncio
        from nio import AsyncClient

        async def do_send():
            client = AsyncClient(self.__homeserver_url, self.__username)
            await client.login(self.__password)
            for room in self.__room_ids:
                for msg in messages:
                    await client.room_send(
                        room_id=room,
                        message_type="m.room.message",
                        content={
                            "msgtype": "m.text",
                            "format": "org.matrix.custom.html",
                            "body": re.sub('<[^<]+?>', '', msg),
                            "formatted_body": msg
                        }
                    )
            await client.close()
        asyncio.get_event_loop().run_until_complete(do_send())
