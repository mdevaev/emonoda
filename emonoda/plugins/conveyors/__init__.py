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


from .. import BasePlugin
from .. import BaseExtension


# =====
class BaseConveyor(BasePlugin):  # pylint: disable=too-many-instance-attributes
    def __init__(self, **_):  # +stub
        self._torrents = None

        self.invalid_count = 0
        self.not_in_client_count = 0
        self.unknown_count = 0
        self.passed_count = 0
        self.updated_count = 0
        self.error_count = 0
        self.exception_count = 0

    # ===

    def set_torrents(self, torrents):
        self._torrents = torrents

    def get_torrents(self):
        raise NotImplementedError

    def read_captcha(self, url):
        raise NotImplementedError

    def print_summary(self):
        raise NotImplementedError

    # ===

    def mark_invalid(self):
        raise NotImplementedError

    def mark_not_in_client(self):
        raise NotImplementedError

    def mark_unknown(self):
        raise NotImplementedError

    def mark_in_progress(self, fetcher):
        raise NotImplementedError

    def mark_passed(self, fetcher):
        raise NotImplementedError

    def mark_updated(self, fetcher, diff):
        raise NotImplementedError

    def mark_fetcher_error(self, fetcher, err):
        raise NotImplementedError

    def mark_exception(self, fetcher):
        raise NotImplementedError


class WithLogs(BaseExtension):
    def __init__(self, log_stdout, log_stderr, **_):  # +stub
        self._log_stdout = log_stdout
        self._log_stderr = log_stderr
