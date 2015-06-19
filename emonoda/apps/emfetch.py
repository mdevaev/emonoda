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
import json
import shutil
import contextlib
import argparse

from ..plugins.fetchers import FetcherError
from ..plugins.fetchers import select_fetcher

from ..helpers import tcollection

from .. import tfile
from .. import fmt

from . import init
from . import get_configured_log
from . import get_configured_conveyor
from . import get_configured_client
from . import get_configured_fetchers


# =====
def backup_torrent(torrent, backup_dir_path, backup_suffix):
    backup_suffix = fmt.format_now(backup_suffix)
    backup_file_path = os.path.join(backup_dir_path, os.path.basename(torrent.get_path()) + backup_suffix)
    shutil.copyfile(torrent.get_path(), backup_file_path)


def make_sub_name(path, prefix, suffix):
    return os.path.join(
        os.path.dirname(path),
        prefix + os.path.basename(path) + suffix,
    )


@contextlib.contextmanager
def client_hooks(client, torrent, to_save_customs, to_set_customs):
    if client is not None:
        prefix = client.get_data_prefix(torrent)
        if len(to_save_customs) != 0:
            customs = client.get_customs(torrent, to_save_customs)
        else:
            customs = {}
        meta_file_path = make_sub_name(torrent.get_path(), ".", ".meta")
        with open(meta_file_path, "w") as meta_file:
            meta_file.write(json.dumps({
                "prefix": prefix,
                "customs": customs,
            }))
        client.remove_torrent(torrent)

    yield  # Torrent-object was changed

    if client is not None:
        client.load_torrent(torrent, prefix)
        customs.update({
            key: fmt.format_now(value)
            for (key, value) in to_set_customs.items()
        })
        if len(customs) != 0:
            client.set_customs(torrent, customs)
        os.remove(meta_file_path)


def update_torrent(client, torrent, new_data, to_save_customs, to_set_customs):
    data_file_path = make_sub_name(torrent.get_path(), ".", ".newdata")
    with open(data_file_path, "wb") as data_file:
        data_file.write(new_data)
    with client_hooks(client, torrent, to_save_customs, to_set_customs):
        os.replace(data_file_path, torrent.get_path())
        torrent.load_from_data(new_data, torrent.get_path())


def update(
    conveyor,
    client,
    fetchers,
    backup_dir_path,
    backup_suffix,
    to_save_customs,
    to_set_customs,
    noop,
):
    hashes = (client.get_hashes() if client is not None else [])

    for torrent in conveyor.get_torrents():
        if torrent is None:
            conveyor.mark_invalid()
            continue

        if client is not None and torrent.get_hash() not in hashes:
            conveyor.mark_not_in_client()
            continue

        fetcher = select_fetcher(torrent, fetchers)
        if fetcher is None:
            conveyor.mark_unknown()
            continue

        conveyor.mark_in_progress(fetcher)

        try:
            if not fetcher.is_torrent_changed(torrent):
                conveyor.mark_passed(fetcher)
                continue

            new_data = fetcher.fetch_new_data(torrent)
            diff = tfile.get_difference(torrent, tfile.Torrent(data=new_data))
            if not noop:
                if backup_dir_path is not None:
                    backup_torrent(torrent, backup_dir_path, backup_suffix)
                update_torrent(client, torrent, new_data, to_save_customs, to_set_customs)

            conveyor.mark_updated(fetcher, diff)

        except FetcherError as err:
            conveyor.mark_fetcher_error(fetcher, err)

        except Exception:
            conveyor.mark_exception(fetcher)

    conveyor.print_summary()


# ===== Main =====
def main():
    (parent_parser, argv, config) = init()
    args_parser = argparse.ArgumentParser(
        prog="emfetch",
        description="Update torrent files from popular trackers",
        parents=[parent_parser],
    )
    args_parser.add_argument("-f", "--name-filter", default="*.torrent", metavar="<wildcard_pattern>")
    args_parser.add_argument("-y", "--only-fetchers", default=[], nargs="+", metavar="<fetcher>")
    args_parser.add_argument("-x", "--exclude-fetchers", default=[], nargs="+", metavar="<fetcher>")
    args_parser.add_argument("--noop", action="store_true")
    options = args_parser.parse_args(argv[1:])

    with get_configured_log(config, False, sys.stdout) as log_stdout:
        with get_configured_log(config, False, sys.stderr) as log_stderr:

            conveyor = get_configured_conveyor(config, log_stdout, log_stderr)

            client = get_configured_client(
                config=config,
                required=False,
                with_customs=(len(config.emfetch.save_customs) or len(config.emfetch.set_customs)),
                log=log_stderr,
            )

            fetchers = get_configured_fetchers(
                config=config,
                captcha_decoder=conveyor.read_captcha,
                only=options.only_fetchers,
                exclude=options.exclude_fetchers,
                log=log_stderr,
            )

            conveyor.set_torrents(tcollection.load_from_dir(
                path=config.core.torrents_dir,
                name_filter=options.name_filter,
                log=log_stderr,
            ))

            update(
                conveyor=conveyor,
                client=client,
                fetchers=fetchers,
                backup_dir_path=config.emfetch.backup_dir,
                backup_suffix=config.emfetch.backup_suffix,
                to_save_customs=config.emfetch.save_customs,
                to_set_customs=config.emfetch.set_customs,
                noop=options.noop,
            )


if __name__ == "__main__":
    main()  # Do the thing!
