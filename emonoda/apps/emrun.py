"""
    Emonoda -- A set of tools to organize and manage your torrents
    Copyright (C) 2015  Devaev Maxim <mdevaev@gmail.com>
    Copyright (C) 2015  Vitaly Lipatov <lav@etersoft.ru>

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
import re

from ..plugins.clients import NoSuchTorrentError

from .. import fmt

from . import init
from . import get_configured_log
from . import get_configured_client

def touch_file(root, f):
    full = os.path.join(root, f)
    if f and not os.path.exists(full):
        d = os.path.dirname(full)
        if d and not os.path.exists(d):
            print("Creating ", d, "dir...")
            os.makedirs(d)
        if f and not os.path.exists(full):
            try:
                tf = open(full, 'wb')
                tf.close()
                print("  File ", full, " OK")
            except:
                raise RuntimeError("Error with ", full)


# ===== Main =====
def main():
    (parent_parser, argv, config) = init()
    args_parser = argparse.ArgumentParser(
        prog="emrun",
        description="Start torrents in client",
        parents=[parent_parser],
    )
    args_parser.add_argument("-v", "--verbose", action="store_true")
    options = args_parser.parse_args(argv[1:])

    with get_configured_log(config, (not options.verbose), sys.stderr) as log_stderr:
        client = get_configured_client(
            config=config,
            required=True,
            with_customs=False,
            log=log_stderr,
        )

        for item in client._client.get_torrents(arguments=("id", "name", "hashString", "status", "error", "errorString", "downloadDir")):
            if item.error == 3:
                match = re.match('^No data', item.errorString)
                if not bool(match):
                    continue
                if item.status != "stopped":
                    continue
                print("", item.id, " ", item.name, " status= ", item.status, " error= ", item.error, ":", bool(match) ," ", item.errorString)

                t = client.get_files(item.hashString)
                for f in t:
                    # Hack due unpredicatable file order
                    if not t[f] == None:
                        touch_file(item.downloadDir, f)

                try:
                    client._client.start_torrent(item.id)
                except KeyError as err:
                    print(str(err))
                print("Start verify and start torrent DONE")


if __name__ == "__main__":
    main()  # Do the thing!
