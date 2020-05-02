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
import uuid
import random

from ..plugins.trackers import BaseTracker

from ..plugins.confetti import UpdateResult
from ..plugins.confetti import ResultsType
from ..plugins.confetti import STATUSES

from ..helpers import surprise

from ..tfile import TorrentsDiff
from ..tfile import Torrent

from . import init
from . import wrap_main
from . import get_configured_log
from . import get_configured_confetti


FORMATS = ("mkv", "jpg", "srt", "ass", "png", "pdf", "exe", "dll")
WORDS = ( 
    "nya", "yay", "neko", "sempai", "sensei", "kitsune", "test", 
    "lain", "imouto", "aneki", "baka"
)
SUFFIXES = ("chan", "kun", "san", "sama")
SEPS = ("_", "-", ".", "...", "__")
DOMAINS = ("org", "com", "ru", "io")
ERRS = (
    ("BadError","Something bad had happened!"),
    ("WaitError", "WAIT OH-"), 
    ("OniiChanError", "Feed me, onii-chan"),
    ("ConnectionError", "Lost connection with reality")
)

def rand_some_range(start=1, end=5):
    return range(random.randint(start, end))


def randsuffix(word):
    if not random.choice((False, True)):
        return word
    return word + "-" + random.choice(SUFFIXES)

def randword():
    return random.choice(WORDS)

def randwords():
    return " ".join([randsuffix(randword()) for i in rand_some_range()])

def randdomain():
    return randword() + "." + random.choice(DOMAINS)


def randfile():
    path = [randwords() for i in rand_some_range(0)]
    path.append(randwords() + "." + random.choice(FORMATS))
    return "/".join(path)

# =====
class FakeTorrent(Torrent):
    def __init__(self, tracker: BaseTracker) -> None:  # pylint: disable=super-init-not-called
        name = randwords()
        domain = random.choice(tracker.PLUGIN_NAMES)
        self.___filename = name.replace(" ", random.choice(SEPS)) + ".torrent"
        self.___name = name + randwords()
        self.___comment = "http://{}/{}".format(domain, uuid.uuid4().hex)

    def get___filename(self):
        return self.___filename

    def get_name(self, surrogate_escape: bool=False) -> str:
        return self.___name

    def get_comment(self) -> str:
        return self.___comment


TRACKERS = []
for i in rand_some_range(2):
    names = [randdomain() for i in rand_some_range()]
    class FakeTracker(BaseTracker):  # pylint: disable=abstract-method
        PLUGIN_NAMES = names

        def __init__(self) -> None:  # pylint: disable=super-init-not-called
            pass
    
    TRACKERS.append(FakeTracker())


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
        results: ResultsType = {}
        for status in STATUSES:
            results[status] = stat_result = {}
            for i in rand_some_range(0):
                tracker = random.choice(TRACKERS)
                torr = FakeTorrent(tracker)
                diff = None
                err=("", "")
                if status == "affected":
                    diff = TorrentsDiff(
                        added=frozenset(randfile() for i in rand_some_range(0)),
                        removed = frozenset(randfile() for i in rand_some_range(0)),
                        modified = frozenset(randfile() for i in rand_some_range(0)),
                        type_modified = frozenset(randfile() for i in rand_some_range(0))
                    )
                if status in ("tracker_error", "unhandled_error"):
                    err = random.choice(ERRS)
                stat_result[torr.get___filename()] = UpdateResult.new(
                    torrent=torr,
                    tracker=tracker,
                    diff=diff,
                    err_msg=err[1],
                    err_name=err[0]
                )

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
