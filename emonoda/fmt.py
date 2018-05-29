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


import math
import datetime

from typing import Tuple
from typing import Generator

from .tfile import TorrentsDiff

from . import tools


# =====
_UNITS = tuple(zip(
    ("bytes", "kB", "MB", "GB", "TB", "PB"),
    (0,       0,    1,    2,    2,    2),
))


# =====
def format_size(size: int) -> str:
    if size > 1:
        exponent = min(int(math.log(size, 1024)), len(_UNITS) - 1)
        quotient = float(size) / 1024 ** exponent
        (unit, decimals) = _UNITS[exponent]
        result = ("{:.%sf} {}" % (decimals)).format(quotient, unit)
    elif size == 0:
        result = "0 bytes"
    elif size == 1:
        result = "1 byte"
    else:
        ValueError("size must be >= 0")
    return result


def format_progress(value: int, limit: int) -> Tuple[str, Tuple[int, int]]:
    return (("{cyan}%%%dd/{yellow}" % (len(str(limit)))) + "%d{reset}", (value, limit))


def format_progress_bar(value: int, limit: int, length: int) -> Tuple[str, Tuple[int, int]]:
    (progress, placeholders) = format_progress(value, limit)
    if value != limit:
        color = "red"
    else:
        color = "green"
    fill = int(value / limit * length)
    pb = "{{cyan}}{percent:5.1f}%% {{{color}}}[{bar}{{reset}}{fill}{{{color}}}]{{reset}} {progress}".format(
        percent=value / limit * 100,
        color=color,
        bar="\u2588" * fill,
        fill="\u00b7" * (length - fill),
        progress=progress,
    )  # https://en.wikipedia.org/wiki/Code_page_437
    return (pb, placeholders)


def format_now(text: str) -> str:
    return datetime.datetime.now().strftime(text)


def format_torrents_diff(diff: TorrentsDiff, prefix: str) -> Tuple[str, Tuple[str, ...]]:
    lines = []
    placeholders: Tuple[str, ...] = ()
    for (sign, color, items) in [
        ("+", "green",  diff.added),
        ("-", "red",    diff.removed),
        ("~", "cyan",   diff.modified),
        ("?", "yellow", diff.type_modified),
    ]:
        for item in tools.sorted_paths(items):
            lines.append("%s{" + color + "}%s{reset} %s")
            placeholders += (prefix, sign, item)
    return ("\n".join(lines), placeholders)


# =====
def make_fan() -> Generator[str, None, None]:
    fan = 0
    while True:
        if fan < 3:
            fan += 1
        else:
            fan = 0
        yield "/-\\|"[fan]
