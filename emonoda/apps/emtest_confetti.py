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
class _FakeTorrent(Torrent):
    def __init__(self) -> None:  # pylint: disable=super-init-not-called
        pass

    def get_comment(self) -> str:
        return "Test, test, test"


class _FakeTracker(BaseTracker):  # pylint: disable=abstract-method
    PLUGIN_NAME = "example.org"

    def __init__(self) -> None:  # pylint: disable=super-init-not-called
        pass


# ===== Main =====
@wrap_main
def main() -> None:
    (_, _, config) = init()
    with get_configured_log(config, False, sys.stderr) as log_stderr:
        results: ResultsType = {
            "affected": {
                "test1.torrent": UpdateResult.new(
                    torrent=_FakeTorrent(),
                    tracker=_FakeTracker(),
                    diff=TorrentsDiff.new(
                        added=set(["nya.mkv", "nya.srt"]),
                        removed=set(["nyaa.srt", "nyaa.mkv"]),
                        type_modified=set(["list.lst"]),
                    ),
                ),
                "test2.torrent": UpdateResult.new(
                    torrent=_FakeTorrent(),
                    tracker=_FakeTracker(),
                    diff=TorrentsDiff.new(
                        added=set(["nya.mkv", "nya.srt"]),
                        removed=set(["nyaa.srt", "nyaa.mkv"]),
                        type_modified=set(["list.lst"]),
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
