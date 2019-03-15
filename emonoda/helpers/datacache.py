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
import pickle

from typing import Dict
from typing import NamedTuple

from ..plugins.clients import BaseClient

from ..tfile import TorrentEntryAttrs

from ..cli import Log

from . import tcollection


# =====
class CacheEntryAttrs(NamedTuple):
    files: Dict[str, TorrentEntryAttrs]
    prefix: str


class TorrentsCache(NamedTuple):
    version: int
    torrents: Dict[str, CacheEntryAttrs]


def get_cache(
    cache_path: str,
    client: BaseClient,
    files_from_client: bool,
    force_rebuild: bool,
    torrents_dir_path: str,
    name_filter: str,
    log: Log,
) -> TorrentsCache:

    cache = _read(cache_path, force_rebuild, log)
    if _update(cache, client, files_from_client, torrents_dir_path, name_filter, log):
        _write(cache, cache_path, log)
    return cache


# =====
def _read(path: str, force_rebuild: bool, log: Log) -> TorrentsCache:
    fallback = TorrentsCache(
        version=0,
        torrents={},
    )
    if force_rebuild or not os.path.exists(path):
        return fallback

    log.info("Reading the cache from {cyan}%s{reset} ...", (path,))
    with open(path, "rb") as cache_file:
        try:
            cache_low = pickle.load(cache_file)
            if cache_low["version"] != fallback.version:
                return fallback
            else:
                return TorrentsCache(
                    version=cache_low["version"],
                    torrents=pickle.loads(cache_low["torrents_pk"]),
                )
        except (KeyError, ValueError, pickle.UnpicklingError):
            log.error("Can't unpickle cache file - ingored: {red}%s{reset}", (path,))
            return fallback


def _write(cache: TorrentsCache, path: str, log: Log) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    log.info("Writing the cache to {cyan}%s{reset} ...", (path,))
    with open(path, "wb") as cache_file:
        pickle.dump({
            "version": cache.version,
            "torrents_pk": pickle.dumps(cache.torrents),
        }, cache_file)


def _update(
    cache: TorrentsCache,
    client: BaseClient,
    files_from_client: bool,
    path: str,
    name_filter: str,
    log: Log,
) -> bool:

    log.info("Fetching all hashes from client ...")
    hashes = client.get_hashes()

    log.info("Validating the cache ...")

    # --- Old ---
    to_remove = sorted(set(cache.torrents).difference(hashes))
    if len(to_remove) != 0:
        for torrent_hash in to_remove:
            cache.torrents.pop(torrent_hash)
        log.info("Removed {magenta}%d{reset} obsolete hashes from cache", (len(to_remove),))

    # --- New ---
    to_add = sorted(set(hashes).difference(cache.torrents))
    added = 0
    if len(to_add) != 0:
        torrents = tcollection.by_hash(tcollection.load_from_dir(path, name_filter, True, log))

        if not log.isatty():
            log.info("Adding files for the new {yellow}%d{reset} hashes ...", (len(to_add),))

        for torrent_hash in log.progress(
            to_add,
            ("Adding files ...", ()),
            ("Added {magenta}%d{reset} new hashes from client", (lambda: added,))
        ):
            torrent = torrents.get(torrent_hash)
            if torrent is not None:
                cache.torrents[torrent_hash] = CacheEntryAttrs(
                    files=(client.get_files(torrent) if files_from_client else torrent.get_files()),
                    prefix=client.get_data_prefix(torrent),
                )
                added += 1
            else:
                log.error("Not cached - missing torrent for: {red}%s{reset} -- %s",
                          (torrent_hash, client.get_file_name(torrent_hash)))

        if not log.isatty() and added != 0:
            log.info("Added {magenta}%d{reset} new hashes from client", (added,))

    return bool(len(to_remove) or added)
