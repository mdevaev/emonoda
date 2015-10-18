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

from ..plugins.clients import NoSuchTorrentError

from ..helpers import tcollection

from .. import tfile

from . import init
from . import get_configured_log
from . import get_configured_client


# ===== Main =====
def main():
    (parent_parser, argv, config) = init()
    args_parser = argparse.ArgumentParser(
        prog="emrm",
        description="Remove a torrent from client",
        parents=[parent_parser],
    )
    args_parser.add_argument("-v", "--verbose", action="store_true")
    args_parser.add_argument("torrents", type=str, nargs="+", metavar="<path/hash>")
    options = args_parser.parse_args(argv[1:])

    with get_configured_log(config, (not options.verbose), sys.stdout) as log_stdout:
        with get_configured_log(config, (not options.verbose), sys.stderr) as log_stderr:
            client = get_configured_client(
                config=config,
                required=True,
                with_customs=False,
                log=log_stderr,
            )

            hashes = []
            for item in tcollection.find(config.core.torrents_dir, options.torrents, True):
                torrent_hash = (item.get_hash() if isinstance(item, tfile.Torrent) else item)
                try:
                    hashes.append((torrent_hash, client.get_file_name(torrent_hash)))
                except NoSuchTorrentError:
                    log_stderr.error("No such torrent: {yellow}%s{reset}", (torrent_hash,))

            if len(hashes) != 0:
                log_stderr.info("Removed:")
                for (torrent_hash, name) in hashes:
                    client.remove_torrent(torrent_hash)
                    log_stdout.print("{yellow}%s{reset} -- %s", (torrent_hash, name))


if __name__ == "__main__":
    main()  # Do the thing!
