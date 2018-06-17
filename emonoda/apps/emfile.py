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
import shlex
import itertools
import argparse
import datetime

from collections import OrderedDict

from typing import List
from typing import Dict
from typing import Callable
from typing import Optional
from typing import Any

from ..plugins.clients import NoSuchTorrentError
from ..plugins.clients import BaseClient
from ..plugins.clients import WithCustoms

from ..helpers import tcollection

from ..tfile import Torrent

from ..cli import Log

from .. import fmt
from .. import tools

from . import StoreTrueOrderedAction
from . import init
from . import wrap_main
from . import get_configured_log
from . import get_configured_client


# =====
def format_size_pretty(torrent: Torrent) -> str:
    return fmt.format_size(torrent.get_size())


def format_announce(torrent: Torrent) -> str:
    return (torrent.get_announce() or "")


def format_announce_list(torrent: Torrent) -> List[str]:
    return list(itertools.chain.from_iterable(torrent.get_announce_list()))


def format_announce_list_pretty(torrent: Torrent) -> str:
    return " ".join(format_announce_list(torrent))


def format_creation_date(torrent: Torrent) -> str:
    return str(torrent.get_creation_date() or "")


def format_creation_date_pretty(torrent: Torrent) -> str:
    date = torrent.get_creation_date()
    return str(datetime.datetime.utcfromtimestamp(date) if date else "")


def format_created_by(torrent: Torrent) -> str:
    return (torrent.get_created_by() or "")


def format_provides(torrent: Torrent) -> List[str]:
    return tools.sorted_paths(torrent.get_files())


def format_is_private(torrent: Torrent) -> str:
    return str(int(torrent.is_private()))


def format_is_private_pretty(torrent: Torrent) -> str:
    return ("yes" if torrent.is_private() else "no")


def _catch_no_such_torrent(
    method: Callable[[Torrent, BaseClient], str],
) -> Callable[[Torrent, Optional[BaseClient]], str]:

    def wrap(torrent: Torrent, client: Optional[BaseClient]) -> str:
        assert client is not None, "Required client"
        try:
            return str(method(torrent, client))
        except NoSuchTorrentError:
            return ""
    return wrap


@_catch_no_such_torrent
def format_client_path(torrent: Torrent, client: BaseClient) -> str:
    return client.get_full_path(torrent)


@_catch_no_such_torrent
def format_client_prefix(torrent: Torrent, client: BaseClient) -> str:
    return client.get_data_prefix(torrent)


def format_client_customs(torrent: Torrent, client: Optional[WithCustoms], customs: List[str]) -> str:
    assert client and WithCustoms in client.get_bases(), "Required client with custom data fields"
    if len(customs) != 0:
        try:
            return " ".join(sorted(
                "{}={}".format(key, shlex.quote(str(value or "")))
                for (key, value) in client.get_customs(torrent, customs).items()
            ))
        except NoSuchTorrentError:
            pass
    return ""


def _make_formatted_tree(files: Dict, _depth: int=0, _prefix: str="    ") -> str:
    text = ""
    for (name, sub) in tools.sorted_paths(files.items(), 0):
        text += _prefix + "*   " * _depth + name + "\n"
        text += _make_formatted_tree(sub, _depth + 1)
    return text


def format_files_tree(torrent: Torrent) -> str:
    tree: Dict = {}
    for path in torrent.get_files():
        parts = os.path.normpath(path).split(os.path.sep)
        local = tree
        for (index, part) in enumerate(parts):
            if index != 0 and len(part) == 0:
                continue
            local.setdefault(part, {})
            local = local[part]
    return _make_formatted_tree(tree)


def print_pretty_all(torrent: Torrent, client: Optional[BaseClient], customs: List[str], log: Log) -> None:
    log.print("{blue}Path:{reset}           %s", (torrent.get_path(),))
    log.print("{blue}Name:{reset}           %s", (torrent.get_name(),))
    log.print("{blue}Hash:{reset}           %s", (torrent.get_hash(),))
    log.print("{blue}Size:{reset}           %s", (format_size_pretty(torrent),))
    log.print("{blue}Announce:{reset}       %s", (format_announce(torrent),))
    log.print("{blue}Announce list:{reset}  %s", (format_announce_list_pretty(torrent),))
    log.print("{blue}Creation date:{reset}  %s", (format_creation_date_pretty(torrent),))
    log.print("{blue}Created by:{reset}     %s", (format_created_by(torrent),))
    log.print("{blue}Private:{reset}        %s", (format_is_private_pretty(torrent),))
    log.print("{blue}Comment:{reset}        %s", (torrent.get_comment(),))
    if client is not None:
        log.print("{blue}Client path:{reset}    %s", (format_client_path(torrent, client),))
        if WithCustoms in client.get_bases() and len(customs) != 0:
            log.print("{blue}Client customs:{reset} %s", (format_client_customs(torrent, client, customs),))  # type: ignore
    if torrent.is_single_file():
        log.print("{blue}Provides:{reset}       %s", (tuple(torrent.get_files())[0],))
    else:
        log.print("{blue}Provides:{reset}\n%s", (format_files_tree(torrent),))


def print_value(header: str, value: Any, without_headers: bool, log: Log) -> None:
    if without_headers:
        log.print("%s", (str(value or ""),))
    else:
        log.print("{blue}%s:{reset} %s", (header, str(value or "")))


# ===== Main =====
@wrap_main
def main() -> None:  # pylint: disable=too-many-locals
    options = config = client = None  # Makes pylint happy
    actions = OrderedDict(
        (option[2:].replace("-", "_"), (option, method))
        for (option, method) in [
            ("--path",                 Torrent.get_path),
            ("--name",                 Torrent.get_name),
            ("--hash",                 Torrent.get_hash),
            ("--comment",              Torrent.get_comment),
            ("--size",                 Torrent.get_size),
            ("--size-pretty",          format_size_pretty),
            ("--announce",             format_announce),
            ("--announce-list",        format_announce_list),
            ("--announce-list-pretty", format_announce_list_pretty),
            ("--creation-date",        format_creation_date),
            ("--creation-date-pretty", format_creation_date_pretty),
            ("--created-by",           format_created_by),
            ("--provides",             format_provides),
            ("--is-private",           format_is_private),
            ("--is-private-pretty",    format_is_private_pretty),
            ("--client-path",          lambda torrent: format_client_path(torrent, client)),
            ("--client-prefix",        lambda torrent: format_client_prefix(torrent, client)),
            ("--client-customs",       lambda torrent: format_client_customs(torrent, client, config.emfile.show_customs)),  # type: ignore
            ("--make-magnet",          lambda torrent: torrent.make_magnet(options.magnet_fields)),  # type: ignore
        ]
    )

    (parent_parser, argv, config) = init()
    args_parser = argparse.ArgumentParser(
        prog="emfile",
        description="Show a metadata of torrent file",
        parents=[parent_parser],
    )
    for (dest, (option, _)) in actions.items():
        args_parser.add_argument(option, dest=dest, action=StoreTrueOrderedAction)
    args_parser.add_argument("--without-headers", action="store_true")
    args_parser.add_argument("--magnet-fields", nargs="+", default=[], metavar="<fields>", choices=["names", "trackers", "size"])
    args_parser.add_argument("-v", "--verbose", action="store_true")
    args_parser.add_argument("torrents", nargs="+", metavar="<path>")
    options = args_parser.parse_args(argv[1:])

    to_print = [
        (actions[dest][0][2:], actions[dest][1])
        for (dest, flag) in getattr(options, "ordered_flags", [])
        if flag
    ]
    torrents = tcollection.find_torrents(config.core.torrents_dir, options.torrents)

    with get_configured_log(config, False, sys.stdout) as log_stdout:
        with get_configured_log(config, (not options.verbose), sys.stderr) as log_stderr:
            client = get_configured_client(
                config=config,
                required=False,
                with_customs=bool(config.emfile.show_customs),
                log=log_stderr,
            )

            for torrent in torrents:
                if len(to_print) == 0:
                    print_pretty_all(torrent, client, config.emfile.show_customs, log_stdout)
                else:
                    for (header, method) in to_print:
                        retval = method(torrent)  # type: ignore
                        if isinstance(retval, (list, tuple)):
                            for item in retval:
                                print_value(header, item, options.without_headers, log_stdout)
                        else:
                            print_value(header, retval, options.without_headers, log_stdout)
                if len(torrents) > 1:
                    log_stdout.print()


if __name__ == "__main__":
    main()  # Do the thing!
