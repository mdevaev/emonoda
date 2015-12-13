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

from .. import tfile


# =====
def load_from_dir(path, name_filter, log):
    if not log.isatty():
        log.info("Loading torrents from {cyan}%s/{yellow}%s{reset} ...", (path, name_filter))

    torrents = {}
    for name in sorted(os.listdir(path)):
        if fnmatch.fnmatch(name, name_filter):
            file_path = os.path.abspath(os.path.join(path, name))
            if log.isatty():
                log.info("Loading torrents from {cyan}%s/{yellow}%s{reset} -- {yellow}%s{reset} ...",
                         (path, name_filter, name), one_line=True)
            try:
                torrents[name] = tfile.Torrent(path=file_path)
            except ValueError:
                log.error("Found broken torrent: {cyan}%s/{yellow}%s{reset}", (path, name))
                torrents[name] = None
            except Exception:
                log.error("Can't process torrent: {cyan}%s/{yellow}%s{reset}", (path, name))
                raise

    log.info("Loaded {magenta}%d{reset} torrents from {cyan}%s/{yellow}%s{reset}",
             (len(torrents), path, name_filter))
    return torrents


def by_hash(torrents):
    return {
        torrent.get_hash(): torrent
        for torrent in filter(None, torrents.values())
    }


def by_hash_with_dups(torrents):
    with_dups = {}
    for torrent in filter(None, torrents.values()):
        with_dups.setdefault(torrent.get_hash(), [])
        with_dups[torrent.get_hash()].append(torrent)
    return with_dups


# =====
def find(path, items, pass_hash):
    return [_find_torrent(path, item, pass_hash) for item in items]


def _find_torrent(path, item, pass_hash):
    if os.path.exists(item):
        return tfile.Torrent(path=os.path.abspath(item))
    if os.path.sep not in item:
        full_path = os.path.join(path, item)
        if os.path.exists(full_path):
            return tfile.Torrent(path=full_path)
    if pass_hash and tfile.is_hash(item.strip()):
        return item.strip()
    raise RuntimeError("Can't find torrent: {}".format(item))
