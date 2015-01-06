import sys
import os
import argparse

from ..core import tfile
from ..core import tools
from ..core import fmt

from . import init
from . import get_configured_client


# ===== Main =====
def main():
    (parent_parser, argv, config) = init()
    args_parser = argparse.ArgumentParser(
        prog="rtdiff",
        description="Show the difference between two torrent files",
        parents=[parent_parser],
    )
    args_parser.add_argument("torrents", type=str, nargs=2, metavar="<path/hash>")
    options = args_parser.parse_args(argv[1:])

    client = get_configured_client(config)

    for count in range(2):
        item = options.torrents[count]
        if os.path.exists(item):
            options.torrents[count] = tfile.Torrent(path=item).get_files()
        elif tfile.is_hash(item):
            if client is None:
                raise RuntimeError("Required client for hash: {}".format(item))
            options.torrents[count] = client.get_files(item)
        else:
            raise RuntimeError("Invalid file or hash: {}".format(item))

    tools.Log(config.core.use_colors, config.core.force_colors, sys.stdout).print(
        fmt.format_torrents_diff(tfile.get_difference(*options.torrents), " "),
    )


if __name__ == "__main__":
    main()
