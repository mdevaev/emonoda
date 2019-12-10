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
import json
import traceback
import operator
import argparse

from typing import List
from typing import Dict
from typing import NamedTuple
from typing import Optional

from ..plugins.clients import BaseClient

from ..plugins.trackers import TrackerError
from ..plugins.trackers import TrackerStat
from ..plugins.trackers import WithStat

from ..helpers import tcollection

from ..tfile import Torrent

from ..cli import CellAlign
from ..cli import Cell
from ..cli import Log

from . import init
from . import wrap_main
from . import get_configured_log
from . import get_configured_client
from . import get_configured_trackers


# =====
class StatRecord(NamedTuple):
    name: str
    status: str
    torrent: Optional[Torrent]
    tracker: Optional[WithStat]
    stat: TrackerStat
    err_name: str
    err_msg: str
    tb_lines: List[str]

    @staticmethod
    def new(
        name: str,
        status: str,
        torrent: Optional[Torrent] = None,
        tracker: Optional[WithStat] = None,
        stat: Optional[TrackerStat] = None,
        err_name: str="",
        err_msg: str="",
        tb_lines: Optional[List[str]] = None,
    ) -> "StatRecord":

        return StatRecord(
            name=name,
            status=status,
            torrent=torrent,
            tracker=tracker,
            stat=(stat or TrackerStat()),
            err_name=err_name,
            err_msg=err_msg,
            tb_lines=(tb_lines or []),
        )


def select_tracker(trackers: List[WithStat], torrent: Torrent) -> Optional[WithStat]:
    for tracker in trackers:
        if tracker.is_matched_for(torrent):
            return tracker  # type: ignore
    return None


def fetch_stat(
    trackers: List[WithStat],
    torrents: Dict[str, Optional[Torrent]],
    log: Log,
) -> List[StatRecord]:

    if not log.isatty():
        log.info("Fetching statistics ...")

    stats: List[StatRecord] = []
    for (name, torrent) in log.progress(
        sorted(torrents.items(), key=operator.itemgetter(0)),
        ("Fetching statistics", ()),
        ("Fetched statistics for {magenta}%d{reset} torrents", (lambda: len(stats),)),
    ):
        if torrent:
            tracker = select_tracker(trackers, torrent)
            if tracker:
                try:
                    record = StatRecord.new(
                        name=name,
                        status="passed",
                        torrent=torrent,
                        tracker=tracker,
                        stat=tracker.fetch_stat(torrent)
                    )
                except Exception as err:
                    record = StatRecord.new(
                        name=name,
                        status=("tracker_error" if isinstance(err, TrackerError) else "unhandled_error"),
                        torrent=torrent,
                        tracker=tracker,
                        err_name=type(err).__name__,
                        err_msg=str(err),
                        tb_lines="".join(traceback.format_exc()).strip().split("\n"),
                    )
            else:
                record = StatRecord.new(name=name, status="unknown", torrent=torrent)
        else:
            record = StatRecord.new(name=name, status="invalid")
        stats.append(record)

    if not log.isatty():
        log.info("Fetched statistics for {magenta}%d{reset} torrents", (len(stats),))
    return stats


def print_stats_table(stats: List[StatRecord], min_seeders: int, log: Log) -> None:
    log.print()
    log.print_table(
        header=[
            Cell(data=col, align=CellAlign.CENTER)
            for col in ["Name", "Tracker", "Seeders", "Leechers", "Status", "Error"]
        ],
        table=[
            [
                Cell(record.name),
                Cell(record.tracker.PLUGIN_NAMES[0] if record.tracker else ""),
                Cell(
                    data=str(record.stat.seeders),
                    colors=("{green}" if record.stat.seeders >= min_seeders else "{red}"),
                    align=CellAlign.RIGHT,
                ),
                Cell(
                    data=str(record.stat.leechers),
                    colors=("{yellow}" if record.stat.leechers else ""),
                    align=CellAlign.RIGHT,
                ),
                Cell(
                    data=record.status,
                    colors=("{green}" if record.status == "passed" else "{red}"),
                ),
                Cell(record.err_msg if record.status == "tracker_error" else ""),
            ]
            for record in sorted(stats, key=(lambda record: (-record.stat.seeders, record.name)))
        ],
    )
    log.print()


def export_stats(stats: List[StatRecord], path: str) -> None:
    with open(path, "w") as export_file:
        json.dump({
            record.name: {
                "status": record.status,
                "torrent": ({
                    "hash": record.torrent.get_hash(),
                    "path": record.torrent.get_path(),
                    "comment": record.torrent.get_comment(),
                } if record.torrent else None),
                "tracker": (record.tracker.PLUGIN_NAMES[0] if record.tracker else ""),
                "stat": record.stat._asdict(),
                "err_name": record.err_name,
                "err_msg": record.err_msg,
                "tb_lines": record.tb_lines,
            }
            for record in stats
        }, export_file, indent=4, sort_keys=True)


def process_torrents(
    client: BaseClient,
    stats: List[StatRecord],
    start_if: str,
    stop_if: str,
    log: Log,
) -> None:

    if not log.isatty():
        log.info("Processing torrents start/stop ...")
        if start_if:
            log.info("Condition start_if is %r", (start_if,))
        if stop_if:
            log.info("Condition stop_if is %r", (stop_if,))

    hashes = client.get_hashes()
    started = 0
    stopped = 0
    ignored = 0
    errors = 0
    for record in log.progress(
        sorted(stats, key=operator.attrgetter("name")),
        ("Processing torrents", ()),
        (
            "Processed {magenta}%d{reset} torrents, started={magenta}%d{reset},"
            " stopped={magenta}%d{reset}, ignored={magenta}%d{reset}, errors={magenta}%d{reset}",
            (lambda: len(stats), lambda: started, lambda: stopped, lambda: ignored, lambda: errors),
        ),
    ):
        if record.torrent.get_hash() in hashes:
            try:
                if start_if and eval_condition(start_if, record):
                    client.start_torrent(record.torrent)
                    started += 1
                if stop_if and eval_condition(stop_if, record):
                    client.stop_torrent(record.torrent)
                    stopped += 1
            except Exception:
                log.print("%s", ("\n".join("\t" + row for row in traceback.format_exc().strip().split("\n")),))
                errors += 1
        else:
            ignored += 1

    if not log.isatty():
        log.info("Processed {magenta}%d{reset} torrents", (len(stats),))


def eval_condition(condition: str, record: StatRecord) -> bool:
    _ = record
    return eval(condition)  # pylint: disable=eval-used


# ===== Main =====
@wrap_main
def main() -> None:
    (parent_parser, argv, config) = init()
    args_parser = argparse.ArgumentParser(
        prog="emstat",
        description="Collect torrents statistics from trackers",
        parents=[parent_parser],
    )
    args_parser.add_argument("-f", "--name-filter", default="", metavar="<wildcard_pattern>")
    args_parser.add_argument("-y", "--only-trackers", default=[], nargs="+", metavar="<tracker>")
    args_parser.add_argument("-x", "--exclude-trackers", default=[], nargs="+", metavar="<tracker>")
    args_parser.add_argument("--fail-on-captcha", action="store_true")
    args_parser.add_argument("--export", default="", metavar="<json_file>")
    args_parser.add_argument("--dont", action="store_true")
    options = args_parser.parse_args(argv[1:])

    with get_configured_log(config, False, sys.stdout) as log_stdout:
        with get_configured_log(config, False, sys.stderr) as log_stderr:
            client = get_configured_client(
                config=config,
                required=True,
                with_customs=False,
                log=log_stderr,
            )
            assert client

            def read_captcha(url: str) -> str:
                if options.fail_on_captcha:
                    raise RuntimeError("Required decoding of captcha but '--fail-on-captcha' specified")
                log_stderr.info("{yellow}Enter the captcha{reset} from [{blue}%s{reset}]: ", (url,), no_nl=True)
                return input()

            trackers: List[WithStat] = get_configured_trackers(  # type: ignore
                config=config,
                captcha_decoder=read_captcha,
                only=options.only_trackers,
                exclude=options.exclude_trackers,
                required_bases=[WithStat],
                fail_bad_tracker=config.emstat.fail_bad_tracker,
                log=log_stderr,
            )

            torrents = tcollection.load_from_dir(
                path=config.core.torrents_dir,
                name_filter=(options.name_filter or config.emupdate.name_filter),
                precalculate_hashes=bool(options.export),
                log=log_stderr,
            )

            stats = fetch_stat(trackers, torrents, log_stderr)

            print_stats_table(stats, config.emstat.min_seeders, log_stdout)
            if options.export:
                export_stats(stats, options.export)

            if not options.dont and (config.emstat.start_if or config.emstat.stop_if):
                process_torrents(  # type: ignore
                    client=client,
                    stats=stats,
                    start_if=config.emstat.start_if,
                    stop_if=config.emstat.stop_if,
                    log=log_stderr,
                )


if __name__ == "__main__":
    main()  # Do the thing!
