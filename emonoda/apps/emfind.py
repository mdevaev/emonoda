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


import sys
import os
import argparse

from typing import List
from typing import Dict

from ..plugins.clients import BaseClient

from ..helpers import tcollection
from ..helpers import datacache

from ..tfile import TorrentEntryAttrs

from ..cli import Log

from .. import fmt
from .. import tools

from . import init
from . import wrap_main
from . import get_configured_log
from . import get_configured_client


# =====
def build_used_files(cache: datacache.TorrentsCache, data_roots: List[str]) -> Dict[str, TorrentEntryAttrs]:
    files: Dict[str, TorrentEntryAttrs] = dict.fromkeys(data_roots, TorrentEntryAttrs.dir())
    for c_attrs in cache.torrents.values():
        prefix = os.path.normpath(c_attrs.prefix)

        for (path, f_attrs) in c_attrs.files.items():
            files[os.path.join(prefix, path)] = f_attrs

        for data_root_path in data_roots:
            if prefix.startswith(data_root_path):
                parts: List[str] = list(filter(None, prefix[len(data_root_path):].split(os.path.sep)))
                for index in range(len(parts)):
                    path = os.path.join(*([data_root_path] + parts[:index + 1]))
                    files[path] = TorrentEntryAttrs.dir()
                break
    return files


def build_all_files(data_root_path: str, log: Log) -> Dict[str, TorrentEntryAttrs]:
    if not log.isatty():
        log.info("Scanning directory {cyan}%s{reset} ...", (data_root_path,))

    files: Dict[str, TorrentEntryAttrs] = {}
    for (prefix, _, local_files) in log.progress(
        os.walk(data_root_path),
        ("Scanning directory {cyan}%s{reset} ...", (data_root_path,)),
        ("Scanned directory {cyan}%s{reset}", (data_root_path,))
    ):
        files[tools.get_decoded_path(prefix)] = TorrentEntryAttrs.dir()
        for name in local_files:
            path = os.path.join(prefix, name)
            try:
                size = os.path.getsize(path)
            except FileNotFoundError:
                continue
            files[tools.get_decoded_path(path)] = TorrentEntryAttrs.file(size)

    if not log.isatty():
        log.info("Scanned directory {cyan}%s{reset}", (data_root_path,))
    return files


# =====
def print_orphaned_files(  # pylint: disable=too-many-locals
    cache: datacache.TorrentsCache,
    data_roots: List[str],
    ignore_orphans: List[str],
    reduce_dirs: bool,
    log_stdout: Log,
    log_stderr: Log,
) -> None:

    all_files = {}
    for data_root_path in data_roots:
        all_files.update(build_all_files(data_root_path, log_stderr))

    log_stderr.info("Transposing the cache: by-hashes -> files ...")
    used_files = build_used_files(cache, data_roots)

    files = set(all_files).difference(used_files)
    for path in list(files):
        for ignored_path in ignore_orphans:
            if path == ignored_path or path.startswith(ignored_path + os.path.sep):
                files.remove(path)
                break

    if len(files) != 0:
        log_stderr.info("Orhpaned files:")
        size = 0
        common_root = "\0"
        for path in tools.sorted_paths(files):
            size += all_files[path].size
            if reduce_dirs:
                if path.startswith(common_root + os.path.sep):
                    continue
                else:
                    common_root = (path if all_files[path].is_dir else "\0")
            line = ("{blue}D" if all_files[path].is_dir else "{magenta}F") + "{reset} %s"
            log_stdout.print(line, (path,))
        log_stderr.info("Found {red}%d{reset} orphaned files = {red}%s{reset}",
                        (len(files), fmt.format_size(size)))
    else:
        log_stderr.info("No orphaned files found")


def print_not_in_client(
    client: BaseClient,
    torrents_dir_path: str,
    name_filter: str,
    log_stdout: Log,
    log_stderr: Log,
) -> None:

    torrents = tcollection.by_hash(tcollection.load_from_dir(
        path=torrents_dir_path,
        name_filter=name_filter,
        precalculate_hashes=True,
        log=log_stderr,
    ))

    log_stderr.info("Fetching all hashes from client ...")
    client_hashes = client.get_hashes()

    not_in_client = set(torrents).difference(client_hashes)
    if len(not_in_client) != 0:
        log_stderr.info("Not in client:")
        for torrent_hash in not_in_client:
            log_stdout.print("%s", (torrents[torrent_hash].get_path(),))
        log_stderr.info("Found {red}%d{reset} unregistered torrents", (len(not_in_client),))
    else:
        log_stderr.info("No unregistered files found")


def print_missing_torrents(
    client: BaseClient,
    torrents_dir_path: str,
    name_filter: str,
    log_stdout: Log,
    log_stderr: Log,
) -> None:

    torrents = tcollection.by_hash(tcollection.load_from_dir(
        path=torrents_dir_path,
        name_filter=name_filter,
        precalculate_hashes=True,
        log=log_stderr,
    ))

    log_stderr.info("Fetching all hashes from client ...")
    client_hashes = client.get_hashes()

    missing_torrents = set(client_hashes).difference(torrents)
    if len(missing_torrents) != 0:
        log_stderr.info("Missing torrents for:")
        for torrent_hash in missing_torrents:
            log_stdout.print("%s -- %s", (torrent_hash, client.get_file_name(torrent_hash)))
        log_stderr.info("Found {red}%d{reset} torrents without torrent-files", (len(missing_torrents),))
    else:
        log_stderr.info("No torrents without torrent-files found")


def print_duplicate_torrents(
    torrents_dir_path: str,
    name_filter: str,
    log_stdout: Log,
    log_stderr: Log,
) -> None:

    torrents = {
        torrent_hash: variants
        for (torrent_hash, variants) in tcollection.by_hash_with_dups(tcollection.load_from_dir(
            path=torrents_dir_path,
            name_filter=name_filter,
            precalculate_hashes=True,
            log=log_stderr,
        )).items()
        if len(variants) > 1
    }
    if len(torrents) != 0:
        for (torrent_hash, variants) in torrents.items():
            log_stdout.print(torrent_hash)
            for torrent in variants:
                log_stdout.print("\t%s", (torrent.get_path(),))
    else:
        log_stderr.info("No duplicate torrents found")


# ===== Main =====
@wrap_main
def main() -> None:
    (parent_parser, argv, config) = init()
    args_parser = argparse.ArgumentParser(
        prog="emfind",
        description="Querying the client",
        parents=[parent_parser],
    )
    commands = args_parser.add_subparsers(dest="cmd")

    commands.add_parser(
        name="rebuild-cache",
        help="Rebuild files cache",
    )

    commands.add_parser(
        name="orphans",
        help="Reduce orphaned files when base directory also orphaned",
    ).add_argument("--no-reduce-dirs", action="store_true")

    commands.add_parser(
        name="not-in-client",
        help="Find torrent files, which are not registered in the client",
    )

    commands.add_parser(
        name="missing-torrents",
        help="Find torrents registered in the client for which there is no torrent files",
    )

    commands.add_parser(
        name="duplicate-torrents",
        help="Find torrent-files with duplicate hashes",
    )

    options = args_parser.parse_args(argv[1:])

    with get_configured_log(config, False, sys.stdout) as log_stdout:
        with get_configured_log(config, False, sys.stderr) as log_stderr:

            def get_client() -> BaseClient:
                return get_configured_client(  # type: ignore
                    config=config,
                    required=True,
                    with_customs=False,
                    log=log_stderr,
                )

            def get_cache(force_rebuild: bool) -> datacache.TorrentsCache:
                return datacache.get_cache(
                    cache_path=config.emfind.cache_file,
                    client=get_client(),
                    files_from_client=config.emfind.files_from_client,
                    force_rebuild=force_rebuild,
                    torrents_dir_path=config.core.torrents_dir,
                    name_filter=config.emfind.name_filter,
                    log=log_stderr,
                )

            if options.cmd == "rebuild-cache":
                get_cache(True)

            elif options.cmd == "orphans":
                print_orphaned_files(
                    cache=get_cache(False),
                    data_roots=[config.core.data_root_dir] + config.core.another_data_root_dirs,
                    ignore_orphans=config.emfind.ignore_orphans,
                    reduce_dirs=(not options.no_reduce_dirs),
                    log_stdout=log_stdout,
                    log_stderr=log_stderr,
                )

            elif options.cmd in ["not-in-client", "missing-torrents"]:
                {
                    "not-in-client":    print_not_in_client,
                    "missing-torrents": print_missing_torrents,
                }[options.cmd](
                    client=get_client(),
                    torrents_dir_path=config.core.torrents_dir,
                    name_filter=config.emfind.name_filter,
                    log_stdout=log_stdout,
                    log_stderr=log_stderr,
                )

            elif options.cmd == "duplicate-torrents":
                print_duplicate_torrents(
                    torrents_dir_path=config.core.torrents_dir,
                    name_filter=config.emfind.name_filter,
                    log_stdout=log_stdout,
                    log_stderr=log_stderr,
                )


if __name__ == "__main__":
    main()  # Do the thing!
