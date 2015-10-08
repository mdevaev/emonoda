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
import json
import shutil
import contextlib
import traceback
import threading
import operator
import argparse

from ..plugins.fetchers import FetcherError
from ..plugins.fetchers import select_fetcher

from ..plugins.confetti import ST

from ..helpers import tcollection
from ..helpers import surprise

from .. import tfile
from .. import fmt

from . import init
from . import get_configured_log
from . import get_configured_client
from . import get_configured_fetchers
from . import get_configured_confetti


# =====
class OpContext:
    def __init__(self, feeder, torrent, fetcher):
        self._feeder = feeder
        self.torrent = torrent
        self.fetcher = fetcher

        self._status = None
        self._result = None

    def done_not_in_client(self):
        self._status = ST.NOT_IN_CLIENT

    def done_updated(self, diff):
        self._status = ST.UPDATED
        self._result = {"diff": diff}

    def __enter__(self):
        self._feeder._start_op()  # pylint: disable=protected-access

    def __exit__(self, exc_type, exc, tb):
        self._feeder._stop_op()  # pylint: disable=protected-access
        if isinstance(exc, FetcherError):
            self._status = ST.ERROR
            self._result = {
                "err_name": type(exc).__name__,
                "err_msg": str(exc),
            }
        elif isinstance(exc, Exception):
            self._status = ST.EXCEPTION
            self._result = {"tb_lines": traceback.format_exception(exc_type, exc, tb)}
        assert exc_type is None, "\n".join(traceback.format_exception(exc_type, exc, tb))
        if self._status is None:
            self._status = ST.PASSED


class Feeder:  # pylint: disable=too-many-instance-attributes
    def __init__(self, fetchers, torrents, show_unknown, show_passed, show_diff, log_stdout, log_stderr):
        self._fetchers = fetchers
        self._torrents = torrents
        self._show_unknown = show_unknown
        self._show_passed = show_passed
        self._show_diff = show_diff
        self._log_stdout = log_stdout
        self._log_stderr = log_stderr

        self._current_count = 0
        self._current_file_name = None
        self._current_torrent = None
        self._current_fetcher = None

        self._fan = fmt.make_fan()
        self._fan_thread = None
        self._stop_fan = threading.Event()

        self._results = {st: {} for st in ST}

    def get_ops(self):
        for (self._current_count, (self._current_file_name, self._current_torrent)) in enumerate(
            sorted(self._torrents.items(), key=operator.itemgetter(0))
        ):
            self._current_fetcher = None

            if self._current_torrent is None:
                self._save_current_result(ST.INVALID, None)
                self._done_invalid()
                continue

            fetcher = select_fetcher(self._current_torrent, self._fetchers)
            if fetcher is None:
                self._save_current_result(ST.UNKNOWN, None)
                self._done_unknown()
                continue
            self._current_fetcher = fetcher

            op = OpContext(self, self._current_torrent, fetcher)
            yield op
            self._save_current_result(op._status, op._result)  # pylint: disable=protected-access
            {
                ST.PASSED:        self._done_passed,
                ST.UPDATED:       self._done_updated,
                ST.NOT_IN_CLIENT: self._done_not_in_client,
                ST.ERROR:         self._done_fetcher_error,
                ST.EXCEPTION:     self._done_exception,
            }[op._status](op._result)  # pylint: disable=protected-access

        self._print_summary()

    def get_results(self):
        return self._results

    def _save_current_result(self, status, result):
        self._results[status][self._current_file_name] = {
            "torrent": self._current_torrent,
            "fetcher": self._current_fetcher,
            "result":  result,
        }

    def _done_invalid(self):
        self._log_stdout.print(*self._format_fail("red", "!", "INVALID_TORRENT"))

    def _done_unknown(self):
        one_line = (not self._show_unknown and self._log_stdout.isatty())
        self._log_stdout.print(*self._format_fail("yellow", " ", "UNKNOWN"), one_line=one_line)

    def _done_passed(self, _):
        one_line = (not self._show_passed and self._log_stdout.isatty())
        self._log_stdout.print(*self._format_status("blue", " "), one_line=one_line)

    def _done_updated(self, result):
        self._log_stdout.print(*self._format_status("green", "+"))
        if self._show_diff:
            self._log_stdout.print(*fmt.format_torrents_diff(result["diff"], "\t"))

    def _done_not_in_client(self, _):
        self._log_stdout.print(*self._format_fail("red", "!", "NOT_IN_CLIENT"))

    def _done_fetcher_error(self, result):
        (line, placeholders) = self._format_status("red", "-")
        line += " :: {red}%s({reset}%s{red}){reset}"
        placeholders += (result["err_name"], result["err_msg"])
        self._log_stdout.print(line, placeholders)

    def _done_exception(self, result):
        self._log_stdout.print(*self._format_status("red", "-"))
        self._log_stdout.print("%s", ("\n".join("\t" + row for row in result["tb_lines"]),))

    def _start_op(self):
        if self._log_stdout.isatty():
            def loop():
                while not self._stop_fan.wait(timeout=0.1):
                    self._log_stdout.print(*self._format_status("magenta", next(self._fan)), one_line=True)
            self._fan_thread = threading.Thread(target=loop, daemon=True)
            self._fan_thread.start()
        else:
            self._log_stdout.print(*self._format_status("magenta", " "))

    def _stop_op(self):
        self._stop_fan.set()
        self._fan_thread.join()
        self._stop_fan.clear()

    def _format_fail(self, color, sign, error):
        return (
            "[{" + color + "}%s{reset}] %s {" + color + "}%s {cyan}%s{reset}",
            (sign, self._format_progress(), error, self._current_file_name),
        )

    def _format_status(self, color, sign):
        return (
            "[{" + color + "}%s{reset}] %s {" + color + "}%s {cyan}%s{reset} -- %s",
            (
                sign, self._format_progress(), self._current_fetcher.get_name(),
                self._current_file_name, (self._current_torrent.get_comment() or ""),
            ),
        )

    def _format_progress(self):
        return fmt.format_progress(self._current_count + 1, len(self._torrents))

    def _print_summary(self):
        self._log_stdout.finish()
        for (msg, st) in (
            ("Updated:       %d", ST.UPDATED),
            ("Passed:        %d", ST.PASSED),
            ("Not in client: %d", ST.NOT_IN_CLIENT),
            ("Unknown:       %d", ST.UNKNOWN),
            ("Invalid:       %d", ST.INVALID),
            ("Errors:        %d", ST.ERROR),
            ("Exceptions:    %d", ST.EXCEPTION),
        ):
            self._log_stderr.info(msg, (len(self._results[st]),))


def backup_torrent(torrent, backup_dir_path, backup_suffix):
    backup_suffix = fmt.format_now(backup_suffix)
    backup_file_path = os.path.join(backup_dir_path, os.path.basename(torrent.get_path()) + backup_suffix)
    shutil.copyfile(torrent.get_path(), backup_file_path)


def make_sub_name(path, prefix, suffix):
    return os.path.join(
        os.path.dirname(path),
        prefix + os.path.basename(path) + suffix,
    )


@contextlib.contextmanager
def client_hooks(client, torrent, to_save_customs, to_set_customs):
    if client is not None:
        prefix = client.get_data_prefix(torrent)
        if len(to_save_customs) != 0:
            customs = client.get_customs(torrent, to_save_customs)
        else:
            customs = {}
        meta_file_path = make_sub_name(torrent.get_path(), ".", ".meta")
        with open(meta_file_path, "w") as meta_file:
            meta_file.write(json.dumps({
                "prefix": prefix,
                "customs": customs,
            }))
        client.remove_torrent(torrent)

    yield  # Torrent-object was changed

    if client is not None:
        client.load_torrent(torrent, prefix)
        customs.update({
            key: fmt.format_now(value)
            for (key, value) in to_set_customs.items()
        })
        if len(customs) != 0:
            client.set_customs(torrent, customs)
        os.remove(meta_file_path)


def update_torrent(client, torrent, new_data, to_save_customs, to_set_customs):
    data_file_path = make_sub_name(torrent.get_path(), ".", ".newdata")
    with open(data_file_path, "wb") as data_file:
        data_file.write(new_data)
    with client_hooks(client, torrent, to_save_customs, to_set_customs):
        os.replace(data_file_path, torrent.get_path())
        torrent.load_from_data(new_data, torrent.get_path())


def update(
    feeder,
    client,
    backup_dir_path,
    backup_suffix,
    to_save_customs,
    to_set_customs,
    noop,
):
    hashes = (client.get_hashes() if client is not None else [])
    for op in feeder.get_ops():
        try:
            with op:
                if op.torrent.get_hash() not in hashes:
                    op.done_not_in_client()
                    continue

                if op.fetcher.is_torrent_changed(op.torrent):
                    new_data = op.fetcher.fetch_new_data(op.torrent)
                    diff = tfile.get_difference(op.torrent, tfile.Torrent(data=new_data))
                    if not noop:
                        if backup_dir_path is not None:
                            backup_torrent(op.torrent, backup_dir_path, backup_suffix)
                        update_torrent(client, op.torrent, new_data, to_save_customs, to_set_customs)
                    op.done_updated(diff)
        except Exception:
            pass


# ===== Main =====
def main():
    (parent_parser, argv, config) = init()
    args_parser = argparse.ArgumentParser(
        prog="emfetch",
        description="Update torrent files from popular trackers",
        parents=[parent_parser],
    )
    args_parser.add_argument("-f", "--name-filter", default="*.torrent", metavar="<wildcard_pattern>")
    args_parser.add_argument("-y", "--only-fetchers", default=[], nargs="+", metavar="<fetcher>")
    args_parser.add_argument("-x", "--exclude-fetchers", default=[], nargs="+", metavar="<fetcher>")
    args_parser.add_argument("--noop", action="store_true")
    args_parser.add_argument("--mute", action="store_true")
    options = args_parser.parse_args(argv[1:])

    with get_configured_log(config, False, sys.stdout) as log_stdout:
        with get_configured_log(config, False, sys.stderr) as log_stderr:

            client = get_configured_client(
                config=config,
                required=False,
                with_customs=(len(config.emfetch.save_customs) or len(config.emfetch.set_customs)),
                log=log_stderr,
            )

            def read_captcha(url):
                log_stderr.info("{yellow}Enter the captcha{reset} from [{blue}%s{reset}]: ", (url,), no_nl=True)
                return input()

            fetchers = get_configured_fetchers(
                config=config,
                captcha_decoder=read_captcha,
                only=options.only_fetchers,
                exclude=options.exclude_fetchers,
                log=log_stderr,
            )

            if not options.mute:
                confetti = get_configured_confetti(
                    config=config,
                    log=log_stderr,
                )

            torrents = tcollection.load_from_dir(
                path=config.core.torrents_dir,
                name_filter=options.name_filter,
                log=log_stderr,
            )

            feeder = Feeder(
                fetchers=fetchers,
                torrents=torrents,
                show_unknown=config.emfetch.show_unknown,
                show_passed=config.emfetch.show_passed,
                show_diff=config.emfetch.show_diff,
                log_stdout=log_stdout,
                log_stderr=log_stderr,
            )

            update(
                feeder=feeder,
                client=client,
                backup_dir_path=config.emfetch.backup_dir,
                backup_suffix=config.emfetch.backup_suffix,
                to_save_customs=config.emfetch.save_customs,
                to_set_customs=config.emfetch.set_customs,
                noop=options.noop,
            )

            if not options.mute:
                results = feeder.get_results()
                if len(results[ST.UPDATED]) != 0:
                    if not surprise.deploy_surprise(
                        app="emfetch",
                        results=results,
                        confetti=confetti,
                        log=log_stderr,
                    ):
                        raise SystemExit(1)


if __name__ == "__main__":
    main()  # Do the thing!
