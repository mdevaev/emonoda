"""
    Emonoda -- The set of tools to organize and manage of your torrents
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
import json

from . import tfile


# =====
def load_torrents_from_dir(path, name_filter, log):
    if log.isatty():
        def load_torrent(file_path):
            log.info("Loading torrents from {cyan}%s/{yellow}%s{reset} -- {yellow}%s{reset} ...",
                     (path, name_filter, os.path.basename(file_path)), one_line=True)
            return tfile.load_torrent_from_path(file_path)
    else:
        log.info("Loading torrents from {cyan}%s/{yellow}%s{reset} ...", (path, name_filter))
        load_torrent = tfile.load_torrent_from_path

    torrents = tfile.load_from_dir(path, name_filter, as_abs=True, loader=load_torrent)

    log.info("Loaded {magenta}%d{reset} torrents from {cyan}%s/{yellow}%s{reset}",
             (len(torrents), path, name_filter))
    return torrents


def get_torrents_by_hash(torrents):
    return {
        torrent.get_hash(): torrent
        for torrent in filter(None, torrents.values())
    }


# =====
def get_client_hashes(client, log):
    log.info("Fetching all hashes from client ...")
    return client.get_hashes()


# =====
def read_torrents_cache(path, rebuild, log):
    fallback = {
        "version":  0,
        "torrents": {},
    }
    if rebuild or not os.path.exists(path):
        return fallback

    log.info("Reading the cache from {cyan}%s{reset} ...", (path,))
    with open(path) as cache_file:
        try:
            cache = json.loads(cache_file.read())
            if cache["version"] != fallback["version"]:
                return fallback
            else:
                return cache
        except (KeyError, ValueError):
            log.error("The cache was damaged - ingored: {red}%s{reset}", (path,))
            return fallback


def write_torrents_cache(cache, path, log):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    log.info("Writing the cache to {cyan}%s{reset} ...", (path,))
    with open(path, "w") as cache_file:
        cache_file.write(json.dumps(cache))


def build_torrents_cache(cache, client, torrents_dir_path, name_filter, log):
    hashes = get_client_hashes(client, log)

    log.info("Validating the cache ...")

    # --- Old ---
    to_remove = tuple(sorted(set(cache["torrents"]).difference(hashes)))
    if len(to_remove) != 0:
        for torrent_hash in to_remove:
            cache["torrents"].pop(torrent_hash)
        log.info("Removed {magenta}%d{reset} obsolete hashes from cache", (len(to_remove),))

    # --- New ---
    to_add = tuple(sorted(set(hashes).difference(cache["torrents"])))
    added = 0
    if len(to_add) != 0:
        torrents = load_torrents_from_dir(torrents_dir_path, name_filter, log)
        torrents = get_torrents_by_hash(torrents)

        if not log.isatty():
            log.info("Adding files for the new {yellow}%d{reset} hashes ...", (len(to_add),))
        for torrent_hash in to_add:
            torrent = torrents.get(torrent_hash)
            if torrent is not None:
                name = os.path.basename(torrent.get_path())
                if log.isatty():
                    log.info("Adding files for {yellow}%s{reset} ...", (name,), one_line=True)
                cache["torrents"][torrent_hash] = {
                    # "name":      name,
                    # "is_single": torrent.is_single_file(),
                    "files":     torrent.get_files(),
                    "prefix":    client.get_data_prefix(torrent),
                }
                added += 1
            else:
                log.error("Not cached - missing torrent for: {red}%s{reset} -- %s",
                          (torrent_hash, client.get_file_name(torrent_hash)))
        if added != 0:
            log.info("Added {magenta}%d{reset} new hashes from client", (added,))

    return bool(len(to_remove) or added)
