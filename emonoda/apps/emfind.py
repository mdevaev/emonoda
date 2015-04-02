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

import chardet

from .. import fmt
from .. import helpers

from . import init
from . import get_configured_log
from . import get_configured_client


# =====
def build_cache(cache_path, rebuild, client, torrents_dir_path, name_filter, log):
    cache = helpers.read_torrents_cache(cache_path, rebuild, log)
    if helpers.build_torrents_cache(cache, client, torrents_dir_path, name_filter, log):
        helpers.write_torrents_cache(cache, cache_path, log)
    return cache


def build_used_files(cache, data_root_path):
    files = {data_root_path: None}
    for info in cache["torrents"].values():
        prefix = os.path.normpath(info["prefix"])

        for (path, meta) in info["files"].items():
            files[os.path.join(prefix, path)] = (meta or {}).get("size")

        if prefix.startswith(data_root_path):
            parts = list(filter(None, prefix[len(data_root_path):].split(os.path.sep)))
            for index in range(len(parts)):
                path = os.path.join(*([data_root_path] + parts[:index + 1]))
                files[path] = None
    return files


def build_all_files(data_root_path):
    files = {}
    for (prefix, _, local_files) in os.walk(data_root_path):
        files[get_decoded_path(prefix)] = None
        for name in local_files:
            path = os.path.join(prefix, name)
            files[get_decoded_path(path)] = os.path.getsize(path)
    return files


def get_decoded_path(path):
    try:
        path.encode()
        return path
    except UnicodeEncodeError:
        path_bytes = os.fsencode(path)
        try:
            return path_bytes.decode("cp1251")
        except UnicodeDecodeError:
            encoding = chardet.detect(path)["encoding"]
            assert encoding is not None, "Can't determine encoding for bytes string: '{}'".format(repr(path_bytes))
            return path_bytes.decode(encoding)


# =====
def print_orphaned_files(cache, data_root_path, dirs_only, log_stdout, log_stderr):
    log_stderr.info("Scanning directory {cyan}%s{reset} ... ", (data_root_path,))
    all_files = build_all_files(data_root_path)

    log_stderr.info("Transposing the cache: by-hashes -> files ...")
    used_files = build_used_files(cache, data_root_path)

    files = set(all_files).difference(used_files)
    if len(files) != 0:
        log_stderr.info("Orhpaned files:")
        size = 0
        for path in sorted(files):
            is_dir = (all_files[path] is None)
            size += (all_files[path] or 0)
            line = ("{blue}D" if is_dir else "{magenta}F") + "{reset} %s"
            if dirs_only and is_dir or not dirs_only:
                log_stdout.print(line, (path,))
        log_stderr.info("Found {red}%d{reset} orphaned files = {red}%s{reset}",
                        (len(files), fmt.format_size(size)))
    else:
        log_stderr.info("No orphaned files founded")


def print_not_in_client(client, torrents_dir_path, name_filter, log_stdout, log_stderr):
    torrents = helpers.load_torrents_from_dir(torrents_dir_path, name_filter, log_stderr)
    torrents = helpers.get_torrents_by_hash(torrents)
    client_hashes = helpers.get_client_hashes(client, log_stderr)

    not_in_client = set(torrents).difference(client_hashes)
    if len(not_in_client) != 0:
        log_stderr.info("Not in client:")
        for torrent_hash in not_in_client:
            log_stdout.print("%s", torrents[torrent_hash].get_path())
        log_stderr.info("Found {red}%d{reset} unregistered torrents", (len(not_in_client),))
    else:
        log_stderr.info("No unregistered files founded")


def print_missing_torrents(client, torrents_dir_path, name_filter, log_stdout, log_stderr):
    torrents = helpers.load_torrents_from_dir(torrents_dir_path, name_filter, log_stderr)
    torrents = helpers.get_torrents_by_hash(torrents)
    client_hashes = helpers.get_client_hashes(client, log_stderr)

    missing_torrents = set(client_hashes).difference(torrents)
    if len(missing_torrents) != 0:
        log_stderr.info("Missing torrents for:")
        for torrent_hash in missing_torrents:
            log_stdout.print("%s -- %s", (torrent_hash, client.get_file_name(torrent_hash)))
        log_stderr.info("Found {red}%d{reset} torrents without torrent-files", (len(missing_torrents),))
    else:
        log_stderr.info("No torrents without torrent-files founded")


# ===== Main =====
def main():
    (parent_parser, argv, config) = init()
    args_parser = argparse.ArgumentParser(
        prog="emfind",
        description="Querying the client",
        parents=[parent_parser],
    )
    args_parser.add_argument("--rebuild-cache", action="store_true")
    commands = args_parser.add_subparsers(dest="cmd")

    commands.add_parser(
        name="orphans",
        help="Find files that do not belong to the client",
    ).add_argument("--dirs-only", action="store_true")

    commands.add_parser(
        name="not-in-client",
        help="Find torrent files, which are not registered in the client",
    )

    commands.add_parser(
        name="missing-torrents",
        help="Find torrents registered in the client for which there is no torrent files",
    )

    options = args_parser.parse_args(argv[1:])

    with get_configured_log(config, False, sys.stdout) as log_stdout:
        with get_configured_log(config, False, sys.stderr) as log_stderr:

            def get_client():
                return get_configured_client(
                    config=config,
                    required=True,
                    with_customs=False,
                    log=log_stderr,
                )

            def get_cache():
                return build_cache(
                    cache_path=config.emfind.cache_file,
                    rebuild=options.rebuild_cache,
                    client=get_client(),
                    torrents_dir_path=config.core.torrents_dir,
                    name_filter=config.emfind.name_filter,
                    log=log_stderr,
                )

            if options.cmd == "orphans":
                print_orphaned_files(
                    cache=get_cache(),
                    data_root_path=config.core.data_root_dir,
                    dirs_only=options.dirs_only,
                    log_stdout=log_stdout,
                    log_stderr=log_stderr,
                )

            elif options.cmd in ("not-in-client", "missing-torrents"):
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


if __name__ == "__main__":
    main()  # Do the thing!
