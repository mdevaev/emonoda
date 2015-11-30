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
import argparse

from ..helpers import tcollection

from .. import tfile
from .. import fmt

from . import init
from . import get_configured_log
from . import get_configured_client


# ===== Main =====
def main():
    (parent_parser, argv, config) = init()
    args_parser = argparse.ArgumentParser(
        prog="emdiff",
        description="Show a difference between two torrent files",
        parents=[parent_parser],
    )
    args_parser.add_argument("-v", "--verbose", action="store_true")
    args_parser.add_argument("torrents", type=str, nargs=2, metavar="<path/hash>")
    options = args_parser.parse_args(argv[1:])

    torrents = tcollection.find(config.core.torrents_dir, options.torrents, True)

    with get_configured_log(config, False, sys.stdout) as log_stdout:
        with get_configured_log(config, (not options.verbose), sys.stderr) as log_stderr:
            client = None
            lists = []
            for item in torrents:
                if isinstance(item, tfile.Torrent):
                    lists.append(item.get_files())
                else:  # Hash
                    if client is None:
                        client = get_configured_client(
                            config=config,
                            required=True,
                            with_customs=False,
                            log=log_stderr,
                        )
                    lists.append(client.get_files(item))
            diff = tfile.get_difference(*lists)  # pylint: disable=no-value-for-parameter
            log_stdout.print(*fmt.format_torrents_diff(diff, " "))


if __name__ == "__main__":
    main()  # Do the thing!
