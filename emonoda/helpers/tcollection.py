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
import fnmatch

from typing import List
from typing import Dict
from typing import Optional
from typing import Union

from ..tfile import Torrent
from ..tfile import is_torrent_hash

from ..cli import Log


# =====
def load_from_dir(path: str, name_filter: str, precalculate_hashes: bool, log: Log) -> Dict[str, Optional[Torrent]]:
    if not log.isatty():
        log.info("Loading torrents from {cyan}%s/{yellow}%s{reset} ...", (path, name_filter))

    torrents: Dict[str, Optional[Torrent]] = {}
    for name in log.progress(
        sorted(name for name in os.listdir(path) if fnmatch.fnmatch(name, name_filter)),
        ("Loading torrents from {cyan}%s/{yellow}%s{reset}", (path, name_filter)),
        ("Loaded {magenta}%d{reset} torrents from {cyan}%s/{yellow}%s{reset}", (lambda: len(torrents), path, name_filter)),
    ):
        file_path = os.path.abspath(os.path.join(path, name))
        try:
            torrents[name] = Torrent(path=file_path)
            if precalculate_hashes:
                torrents[name].get_hash()  # type: ignore
        except ValueError:
            log.error("Found broken torrent: {cyan}%s/{yellow}%s{reset}", (path, name))
            torrents[name] = None
        except Exception:
            log.error("Can't process torrent: {cyan}%s/{yellow}%s{reset}", (path, name))
            raise

    if not log.isatty():
        log.info("Loaded {magenta}%d{reset} torrents from {cyan}%s/{yellow}%s{reset}",
                 (len(torrents), path, name_filter))
    return torrents


def by_hash(torrents: Dict[str, Optional[Torrent]]) -> Dict[str, Torrent]:
    return {
        torrent.get_hash(): torrent
        for torrent in filter(None, torrents.values())
    }


def by_hash_with_dups(torrents: Dict[str, Optional[Torrent]]) -> Dict[str, List[Torrent]]:
    with_dups: Dict[str, List[Torrent]] = {}  # noqa: E701
    for torrent in filter(None, torrents.values()):
        with_dups.setdefault(torrent.get_hash(), [])
        with_dups[torrent.get_hash()].append(torrent)
    return with_dups


# =====
def find_torrents(path: str, items: str) -> List[Torrent]:
    return [_find_torrent_or_hash(path, item, False) for item in items]  # type: ignore


def find_torrents_or_hashes(path: str, items: str) -> List[Union[Torrent, str]]:
    return [_find_torrent_or_hash(path, item, True) for item in items]


def _find_torrent_or_hash(path: str, item: str, pass_hash: bool) -> Union[Torrent, str]:
    if os.path.exists(item):
        return Torrent(path=os.path.abspath(item))
    if os.path.sep not in item:
        full_path = os.path.join(path, item)
        if os.path.exists(full_path):
            return Torrent(path=full_path)
    if pass_hash and is_torrent_hash(item.strip()):
        return item.strip()
    raise RuntimeError("Can't find torrent: {}".format(item))
