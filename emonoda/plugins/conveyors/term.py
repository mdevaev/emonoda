"""
    Emonoda -- The set of tools to organize and manage your torrents
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


import threading
import operator

from ...optconf import Option

from ... import fmt

from . import BaseConveyor
from . import WithLogs


# =====
class Plugin(BaseConveyor, WithLogs):  # pylint: disable=too-many-instance-attributes
    def __init__(self, show_unknown, show_passed, show_diff, **kwargs):  # pylint: disable=super-init-not-called
        self._init_bases(**kwargs)

        self._show_unknown = show_unknown
        self._show_passed = show_passed
        self._show_diff = show_diff

        self._current_count = 0
        self._current_file_name = None
        self._current_torrent = None

        self._fan = fmt.make_fan()
        self._fan_thread = None
        self._stop_fan = threading.Event()

    @classmethod
    def get_name(cls):
        return "term"

    @classmethod
    def get_options(cls):
        return cls._get_merged_options({
            "show_unknown": Option(default=False, help="Show the torrents with unknown tracker in the log"),
            "show_passed":  Option(default=False, help="Show the torrents without changes"),
            "show_diff":    Option(default=True, help="Show diff between old and updated torrent files"),
        })

    # ===

    def get_torrents(self):
        for (count, (file_name, torrent)) in enumerate(sorted(self._torrents.items(), key=operator.itemgetter(0))):
            self._current_count = count
            self._current_file_name = file_name
            self._current_torrent = torrent
            self._kill_thread()
            yield torrent
        self._kill_thread()

    def read_captcha(self, url):
        self._kill_thread()
        self._log_stderr.info("{yellow}Enter the captcha{reset} from [{blue}%s{reset}]: ", (url,), no_nl=True)
        return input()

    def print_summary(self):
        self._kill_thread()
        self._log_stderr.info("Invalid:       %d", (self.invalid_count,))
        self._log_stderr.info("Not in client: %d", (self.not_in_client_count,))
        self._log_stderr.info("Unknown:       %d", (self.unknown_count,))
        self._log_stderr.info("Passed:        %d", (self.passed_count,))
        self._log_stderr.info("Updated:       %d", (self.updated_count,))
        self._log_stderr.info("Errors:        %d", (self.error_count,))
        self._log_stderr.info("Exceptions:    %d", (self.exception_count,))

    # ===

    def mark_invalid(self):
        self._kill_thread()
        self._log_stdout.print(*self._format_fail("red", "!", "INVALID_TORRENT"))
        self.invalid_count += 1

    def mark_not_in_client(self):
        self._kill_thread()
        self._log_stdout.print(*self._format_fail("red", "!", "NOT_IN_CLIENT"))
        self.not_in_client_count += 1

    def mark_unknown(self):
        self._kill_thread()
        self._log_stdout.print(*self._format_fail("yellow", " ", "UNKNOWN"), one_line=(not self._show_unknown))
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
            self._log_stdout.print(*self._format_status("magenta", " ", fetcher), one_line=True)

    def mark_passed(self, fetcher):
        self._kill_thread()
        self._log_stdout.print(*self._format_status("blue", " ", fetcher), one_line=(not self._show_passed))
        self.passed_count += 1

    def mark_updated(self, fetcher, diff):
        self._kill_thread()
        self._log_stdout.print(*self._format_status("green", "+", fetcher))
        if self._show_diff:
            self._log_stdout.print(*fmt.format_torrents_diff(diff, "\t"))
        self.updated_count += 1

    def mark_fetcher_error(self, fetcher, err):
        self._kill_thread()
        (line, placeholders) = self._format_status("red", "-", fetcher)
        line += " :: {red}%s({reset}%s{red}){reset}"
        placeholders += (type(err).__name__, err)
        self._log_stdout.print(line, placeholders)
        self.error_count += 1

    def mark_exception(self, fetcher):
        self._kill_thread()
        self._log_stdout.print(*self._format_status("red", "-", fetcher))
        self._log_stdout.print("%s", (fmt.format_traceback("\t"),))
        self.exception_count += 1

    # ===

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
