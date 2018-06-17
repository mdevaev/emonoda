"""
    Emonoda -- A set of tools to organize and manage your torrents
    Copyright (C) 2016  Devaev Maxim <mdevaev@gmail.com>

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

from ..plugins.trackers import BaseTracker

from ..plugins.confetti import UpdateResult
from ..plugins.confetti import ResultsType

from ..helpers import surprise

from ..tfile import TorrentsDiff
from ..tfile import Torrent

from . import init
from . import wrap_main
from . import get_configured_log
from . import get_configured_confetti


# =====
class FakeTorrent(Torrent):
    def __init__(self) -> None:  # pylint: disable=super-init-not-called
        pass

    def get_name(self, surrogate_escape: bool=False) -> str:
        return "foobar"

    def get_comment(self) -> str:
        return "http://example.com"


class FakeTracker(BaseTracker):  # pylint: disable=abstract-method
    PLUGIN_NAMES = ["example.org"]

    def __init__(self) -> None:  # pylint: disable=super-init-not-called
        pass


# ===== Main =====
@wrap_main
def main() -> None:
    (parent_parser, argv, config) = init()
    args_parser = argparse.ArgumentParser(
        prog="emconfetti-demo",
        description="Send demo notifications",
        parents=[parent_parser],
    )
    args_parser.add_argument("-y", "--only-confetti", default=[], nargs="+", metavar="<tracker>")
    args_parser.add_argument("-x", "--exclude-confetti", default=[], nargs="+", metavar="<tracker>")
    options = args_parser.parse_args(argv[1:])

    with get_configured_log(config, False, sys.stderr) as log_stderr:
        results: ResultsType = {
            "affected": {
                "test1.torrent": UpdateResult.new(
                    torrent=FakeTorrent(),
                    tracker=FakeTracker(),
                    diff=TorrentsDiff(
                        added=frozenset(["nya.mkv", "nya.srt"]),
                        removed=frozenset(["nyaa.srt", "nyaa.mkv"]),
                        type_modified=frozenset(["list.lst"]),
                    ),
                ),
                "test2.torrent": UpdateResult.new(
                    torrent=FakeTorrent(),
                    tracker=FakeTracker(),
                    diff=TorrentsDiff(
                        added=frozenset(["nya.mkv", "nya.srt"]),
                        removed=frozenset(["nyaa.srt", "nyaa.mkv"]),
                        type_modified=frozenset(["list.lst"]),
                    ),
                ),
            },
            "passed":          {},
            "not_in_client":   {},
            "unknown":         {},
            "invalid":         {},
            "tracker_error":   {},
            "unhandled_error": {},
        }

        confetti = get_configured_confetti(
            config=config,
            only=options.only_confetti,
            exclude=options.exclude_confetti,
            log=log_stderr,
        )

        surprise.deploy_surprise(
            source="emupdate",
            results=results,
            confetti=confetti,
            log=log_stderr,
        )


if __name__ == "__main__":
    main()  # Do the thing!
