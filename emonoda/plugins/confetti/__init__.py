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


import os
import pkgutil
import textwrap
import urllib.request

from typing import List
from typing import Dict
from typing import NamedTuple
from typing import Optional
from typing import Union
from typing import Type
from typing import Any

import mako.template

from ...optconf import Option

from ...plugins.trackers import BaseTracker  # FIXME

from ...tfile import TorrentsDiff
from ...tfile import Torrent

from ... import web

from .. import BasePlugin
from .. import get_classes


# =====
def templated(name: str, built_in: bool=True, **kwargs: Any) -> str:
    if built_in:
        data = pkgutil.get_data(__name__, os.path.join("templates", name))
        assert data, (data, name, __name__)
        text = data.decode()
    else:
        with open(name) as template_file:
            text = template_file.read()
    template = textwrap.dedent(text).strip()
    return mako.template.Template(template).render(**kwargs).strip()


# =====
class _InnerUpdateResult(NamedTuple):
    torrent: Optional[Torrent]
    tracker: Optional[BaseTracker]
    diff: TorrentsDiff
    err_name: str
    err_msg: str
    tb_lines: List[str]


class UpdateResult(_InnerUpdateResult):
    @staticmethod
    def new(
        torrent: Optional[Torrent]=None,
        tracker: Optional[BaseTracker]=None,
        diff: Optional[TorrentsDiff]=None,
        err_name: str="",
        err_msg: str="",
        tb_lines: Optional[List[str]]=None,
    ) -> "UpdateResult":

        return UpdateResult(
            torrent=torrent,
            tracker=tracker,
            diff=(diff or TorrentsDiff.new()),
            err_name=err_name,
            err_msg=err_msg,
            tb_lines=(tb_lines or []),
        )


ResultsType = Dict[str, Dict[str, UpdateResult]]


class BaseConfetti(BasePlugin):
    def send_results(self, source: str, results: ResultsType) -> None:
        raise NotImplementedError


class WithWeb(BaseConfetti):  # pylint: disable=abstract-method
    _SITE_RETRY_CODES: List[int] = []

    def __init__(  # pylint: disable=super-init-not-called
        self,
        timeout: float,
        retries: int,
        retries_sleep: float,
        user_agent: str,
        proxy_url: str,
    ) -> None:

        self.__timeout = timeout
        self.__retries = retries
        self.__retries_sleep = retries_sleep
        self.__user_agent = user_agent
        self.__proxy_url = proxy_url

        self.__opener: Optional[urllib.request.OpenerDirector] = None

    @classmethod
    def get_options(cls) -> Dict[str, Option]:
        return {
            "timeout":       Option(default=10.0, help="Network timeout"),
            "retries":       Option(default=5, help="Retries for failed attempts"),
            "retries_sleep": Option(default=1.0, help="Sleep interval between failed attempts"),
            "user_agent":    Option(default="Mozilla/5.0", help="User-Agent for site"),
            "proxy_url":     Option(default="", help="URL of HTTP/SOCKS4/SOCKS5 proxy"),
        }

    def _init_opener(self) -> None:
        assert not self.__opener
        self.__opener = web.build_opener(self.__proxy_url)

    def _read_url(
        self,
        url: str,
        data: Optional[bytes]=None,
        headers: Optional[Dict[str, str]]=None,
    ) -> bytes:

        assert self.__opener
        headers = (headers or {})
        headers.setdefault("User-Agent", self.__user_agent)
        return web.read_url(
            opener=self.__opener,
            url=url,
            data=data,
            headers=headers,
            timeout=self.__timeout,
            retries=self.__retries,
            retries_sleep=self.__retries_sleep,
            retry_codes=self._SITE_RETRY_CODES,
        )


def get_confetti_class(name: str) -> Type[BaseConfetti]:
    return get_classes("confetti")[name]  # type: ignore
