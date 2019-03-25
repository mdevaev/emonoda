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

from ....plugins.clients.transmission import Plugin as TransmissionClient

from ... import init
from ... import get_configured_log
from ... import get_configured_client


# ===== Main =====
def main() -> None:
    (parent_parser, argv, config) = init()
    args_parser = argparse.ArgumentParser(
        prog="emhook-transmission-redownload",
        description="Start torrents in client",
        parents=[parent_parser],
    )
    args_parser.add_argument("-v", "--verbose", action="store_true")
    options = args_parser.parse_args(argv[1:])

    with get_configured_log(config, False, sys.stdout) as log_stdout:
        with get_configured_log(config, (not options.verbose), sys.stderr) as log_stderr:
            client: TransmissionClient = get_configured_client(  # type: ignore
                config=config,
                required=True,
                with_customs=False,
                log=log_stderr,
            )
            if "transmission" not in client.PLUGIN_NAMES:
                raise RuntimeError("Only for Transmission")

            for obj in client._client.get_torrents(arguments=[  # pylint: disable=protected-access
                "id",
                "name",
                "hashString",
                "status",
                "error",
                "errorString",
                "downloadDir",
            ]):
                if obj.error == 3 and obj.errorString.startswith("No data") and obj.status == "stopped":
                    log_stdout.print("[%s] %s: status=%s; error=%s (%s)", (obj.id, obj.name, obj.status, obj.error, obj.errorString))

                    for (path, attr) in client.get_files(obj.hashString).items():
                        if not attr.is_dir:
                            file_path = os.path.join(obj.downloadDir, path)
                            dir_path = os.path.dirname(file_path)
                            if not os.path.exists(dir_path):
                                os.makedirs(dir_path)
                                log_stdout.print("    Creating dir: %s", (dir_path,))
                            if not os.path.exists(file_path):
                                log_stdout.print("      Creating file: %s", (file_path,))
                                open(file_path, "w").close()

                    try:
                        client._client.start_torrent(obj.id)  # pylint: disable=protected-access
                    except KeyError as err:
                        log_stdout.print("Start error: %s", (str(err),))
                    else:
                        log_stdout.print("Start verify and start torrent DONE")


if __name__ == "__main__":
    main()  # Do the thing!
