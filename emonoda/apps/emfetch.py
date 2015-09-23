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
import threading
import operator
import argparse

from ..plugins.fetchers import FetcherError
from ..plugins.fetchers import select_fetcher

from ..helpers import tcollection

from .. import tfile
from .. import fmt

from . import init
from . import get_configured_log
from . import get_configured_client
from . import get_configured_fetchers


# =====
class Feeder:  # pylint: disable=too-many-instance-attributes
    def __init__(self, torrents, show_unknown, show_passed, show_diff, log_stdout, log_stderr):
        self._torrents = torrents
        self._show_unknown = show_unknown
        self._show_passed = show_passed
        self._show_diff = show_diff
        self._log_stdout = log_stdout
        self._log_stderr = log_stderr

        self._current_count = 0
        self._current_file_name = None
        self._current_torrent = None

        self._fan = fmt.make_fan()
        self._fan_thread = None
        self._stop_fan = threading.Event()

        self.invalid_count = 0
        self.not_in_client_count = 0
        self.unknown_count = 0
        self.passed_count = 0
        self.updated_count = 0
        self.error_count = 0
        self.exception_count = 0

    def get_torrents(self):
        for (count, (file_name, torrent)) in enumerate(sorted(self._torrents.items(), key=operator.itemgetter(0))):
            self._current_count = count
            self._current_file_name = file_name
            self._current_torrent = torrent
            self._kill_thread()
            yield torrent
        self._kill_thread()

    def done_invalid(self):
        self._kill_thread()
        self._log_stdout.print(*self._format_fail("red", "!", "INVALID_TORRENT"))
        self.invalid_count += 1

    def done_not_in_client(self):
        self._kill_thread()
        self._log_stdout.print(*self._format_fail("red", "!", "NOT_IN_CLIENT"))
        self.not_in_client_count += 1

    def done_unknown(self):
        self._kill_thread()
        one_line = (not self._show_unknown and self._log_stdout.isatty())
        self._log_stdout.print(*self._format_fail("yellow", " ", "UNKNOWN"), one_line=one_line)
        self.unknown_count += 1

    def mark_in_progress(self, fetcher):
        self._kill_thread()
        if self._log_stdout.isatty():
            def loop():
                while not self._stop_fan.wait(timeout=0.1):
                    self._log_stdout.print(*self._format_status("magenta", next(self._fan), fetcher), one_line=True)
            self._fan_thread = threading.Thread(target=loop, daemon=True)
            self._fan_thread.start()
        else:
            self._log_stdout.print(*self._format_status("magenta", " ", fetcher))

    def done_passed(self, fetcher):
        self._kill_thread()
        one_line = (not self._show_passed and self._log_stdout.isatty())
        self._log_stdout.print(*self._format_status("blue", " ", fetcher), one_line=one_line)
        self.passed_count += 1

    def done_updated(self, fetcher, diff):
        self._kill_thread()
        self._log_stdout.print(*self._format_status("green", "+", fetcher))
        if self._show_diff:
            self._log_stdout.print(*fmt.format_torrents_diff(diff, "\t"))
        self.updated_count += 1

    def done_fetcher_error(self, fetcher, err):
        self._kill_thread()
        (line, placeholders) = self._format_status("red", "-", fetcher)
        line += " :: {red}%s({reset}%s{red}){reset}"
        placeholders += (type(err).__name__, err)
        self._log_stdout.print(line, placeholders)
        self.error_count += 1

    def done_exception(self, fetcher):
        self._kill_thread()
        self._log_stdout.print(*self._format_status("red", "-", fetcher))
        self._log_stdout.print("%s", (fmt.format_traceback("\t"),))
        self.exception_count += 1

    def print_summary(self):
        self._kill_thread()
        self._log_stdout.finish()
        self._log_stderr.info("Updated:       %d", (self.updated_count,))
        self._log_stderr.info("Passed:        %d", (self.passed_count,))
        self._log_stderr.info("Not in client: %d", (self.not_in_client_count,))
        self._log_stderr.info("Unknown:       %d", (self.unknown_count,))
        self._log_stderr.info("Invalid:       %d", (self.invalid_count,))
        self._log_stderr.info("Errors:        %d", (self.error_count,))
        self._log_stderr.info("Exceptions:    %d", (self.exception_count,))

    def _kill_thread(self):
        if self._fan_thread is not None:
            self._stop_fan.set()
            self._fan_thread.join()
            self._fan_thread = None
            self._stop_fan.clear()

    def _format_fail(self, color, sign, error):
        return (
            "[{" + color + "}%s{reset}] %s {" + color + "}%s {cyan}%s{reset}",
            (sign, self._format_progress(), error, self._current_file_name),
        )

    def _format_status(self, color, sign, fetcher):
        return (
            "[{" + color + "}%s{reset}] %s {" + color + "}%s {cyan}%s{reset} -- %s",
            (
                sign, self._format_progress(), fetcher.get_name(),
                self._current_file_name, (self._current_torrent.get_comment() or ""),
            ),
        )

    def _format_progress(self):
        return fmt.format_progress(self._current_count + 1, len(self._torrents))


# ===
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


# ===
def update(
    feeder,
    client,
    fetchers,
    backup_dir_path,
    backup_suffix,
    to_save_customs,
    to_set_customs,
    noop,
):
    hashes = (client.get_hashes() if client is not None else [])

    for torrent in feeder.get_torrents():
        if torrent is None:
            feeder.done_invalid()
            continue

        if client is not None and torrent.get_hash() not in hashes:
            feeder.done_not_in_client()
            continue

        fetcher = select_fetcher(torrent, fetchers)
        if fetcher is None:
            feeder.done_unknown()
            continue

        feeder.mark_in_progress(fetcher)

        try:
            if not fetcher.is_torrent_changed(torrent):
                feeder.done_passed(fetcher)
                continue

            new_data = fetcher.fetch_new_data(torrent)
            diff = tfile.get_difference(torrent, tfile.Torrent(data=new_data))
            if not noop:
                if backup_dir_path is not None:
                    backup_torrent(torrent, backup_dir_path, backup_suffix)
                update_torrent(client, torrent, new_data, to_save_customs, to_set_customs)

            feeder.done_updated(fetcher, diff)

        except FetcherError as err:
            feeder.done_fetcher_error(fetcher, err)

        except Exception:
            feeder.done_exception(fetcher)

    feeder.print_summary()


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

            feeder = Feeder(
                torrents=tcollection.load_from_dir(
                    path=config.core.torrents_dir,
                    name_filter=options.name_filter,
                    log=log_stderr,
                ),
                show_unknown=config.emfetch.show_unknown,
                show_passed=config.emfetch.show_passed,
                show_diff=config.emfetch.show_diff,
                log_stdout=log_stdout,
                log_stderr=log_stderr,
            )

            update(
                feeder=feeder,
                client=client,
                fetchers=fetchers,
                backup_dir_path=config.emfetch.backup_dir,
                backup_suffix=config.emfetch.backup_suffix,
                to_save_customs=config.emfetch.save_customs,
                to_set_customs=config.emfetch.set_customs,
                noop=options.noop,
            )


if __name__ == "__main__":
    main()  # Do the thing!
