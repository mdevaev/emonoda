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
    def __init__(self, timeout: float, retries: int, retries_sleep: float, **_: Any) -> None:  # pylint: disable=super-init-not-called
        self._timeout = timeout
        self._retries = retries
        self._retries_sleep = retries_sleep

    @classmethod
    def get_options(cls) -> Dict[str, Option]:
        return {
            "timeout":       Option(default=10.0, help="Network timeout"),
            "retries":       Option(default=5, help="Retries for failed attempts"),
            "retries_sleep": Option(default=1.0, help="Sleep interval between failed attempts"),
        }

    def send_results(self, source: str, results: ResultsType) -> None:
        raise NotImplementedError


class WithProxy(BaseConfetti):  # pylint: disable=abstract-method
    def __init__(self, proxy_url: str, **_: Any) -> None:  # pylint: disable=super-init-not-called
        self._proxy_url = proxy_url

    @classmethod
    def get_options(cls) -> Dict[str, Option]:
        return {
            "proxy_url": Option(default="", help="URL of HTTP/SOCKS4/SOCKS5 proxy"),
        }


def get_confetti_class(name: str) -> Type[BaseConfetti]:
    return get_classes("confetti")[name]  # type: ignore
