"""
    rtfetch -- The set of tools to organize and manage your torrents
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
def build_cache(cache_path, client, torrents_dir_path, name_filter, log):
    torrents = helpers.load_torrents_from_dir(torrents_dir_path, name_filter, log)
    cache = helpers.read_torrents_cache(cache_path, log)
    if helpers.rebuild_torrents_cache(client, torrents, cache, log):
        helpers.write_torrents_cache(cache_path, cache, log)
    return cache


def build_used_files(cache, data_dir_path):
    files = {data_dir_path: None}
    for info in cache["torrents"].values():
        prefix = os.path.normpath(info["prefix"])

        for (path, meta) in info["files"].items():
            files[os.path.join(prefix, path)] = (meta or {}).get("size")

        if prefix.startswith(data_dir_path):
            parts = list(filter(None, prefix[len(data_dir_path):].split(os.path.sep)))
            for index in range(len(parts)):
                path = os.path.join(*([data_dir_path] + parts[:index + 1]))
                files[path] = None
    return files


def build_all_files(data_dir_path):
    files = {}
    for (prefix, _, local_files) in os.walk(data_dir_path):
        files[get_decoded(prefix)] = None
        for name in local_files:
            path = os.path.join(prefix, name)
            files[get_decoded(path)] = os.path.getsize(path)
    return files


def get_decoded(path):
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


def print_orphaned_files(cache, data_dir_path, log_stdout, log_stderr):
    all_files = build_all_files(data_dir_path)
    used_files = build_used_files(cache, data_dir_path)
    files = set(all_files).difference(used_files)
    if len(files) != 0:
        log_stderr.print("# Orhpaned files:")
        size = 0
        for path in sorted(files):
            size += (all_files[path] or 0)
            path_type = ("{blue}D" if all_files[path] is None else "{magenta}F") + "{reset}"
            log_stdout.print("%s %s" % (path_type, path))
        log_stderr.print("# Found {red}%d{reset} orphaned files = {red}%s{reset}" % (
                         len(files), fmt.format_size(size)))
    else:
        log_stderr.print("# No orphaned files founded")


# ===== Main =====
def main():
    (parent_parser, argv, config) = init()
    args_parser = argparse.ArgumentParser(
        prog="rtquery",
        description="Querying the client",
        parents=[parent_parser],
    )
    args_parser.add_argument("-f", "--name-filter", default="*.torrent", metavar="<wildcard_pattern>")
    args_parser.add_argument("-v", "--verbose", action="store_true")
    options = args_parser.parse_args(argv[1:])

    with get_configured_log(config, False, sys.stdout) as log_stdout:
        with get_configured_log(config, (not options.verbose), sys.stderr) as log_stderr:

            client = get_configured_client(config, log_stderr, with_customs=False)
            if client is None:
                raise RuntimeError("Required client")

            cache = build_cache(
                cache_path=config.rtquery.cache_file,
                client=client,
                torrents_dir_path=config.core.torrents_dir,
                name_filter=options.name_filter,
                log=log_stderr,
            )

            log_stderr.print("# Processing...")

            print_orphaned_files(cache, config.core.data_dir, log_stdout, log_stderr)


if __name__ == "__main__":
    main()  # Do the thing!
