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
import re
import threading

from colorama import Fore
from colorama import Style

from . import fmt


# =====
_COLORS = {
    "red":     Style.BRIGHT + Fore.RED,
    "green":   Style.BRIGHT + Fore.GREEN,
    "yellow":  Style.BRIGHT + Fore.YELLOW,
    "cyan":    Style.BRIGHT + Fore.CYAN,
    "magenta": Style.BRIGHT + Fore.MAGENTA,
    "blue":    Style.BRIGHT + Fore.BLUE,
    "reset":   Fore.RESET,
}

_NO_COLORS = dict.fromkeys(list(_COLORS), "")


# =====
class Log:
    def __init__(self, use_colors=True, force_colors=False, quiet=False, output=sys.stdout):
        self._quiet = quiet
        self._output = output
        self._fill = 0
        self._colored = (use_colors and (self.isatty() or force_colors))
        self._ansi_regexp = re.compile(r"(\x1b[^m]*m)")

    def isatty(self):
        return self._output.isatty()

    def info(self, text, *args, **kwargs):
        self.print("# {green}I{reset}: " + text, *args, **kwargs)

    def error(self, text, *args, **kwargs):
        self.print("# {red}E{reset}: " + text, *args, **kwargs)

    def print(self, text="", placeholders=(), one_line=False, no_nl=False):
        if not self._quiet:
            rendered = self._format_text(text, placeholders, self._colored)
            view_len = len(self._format_text(text, placeholders, False) if self._colored else rendered)

            cut = 0
            if one_line and self.isatty():
                max_len = self._get_term_width()
                if max_len is not None and view_len > max_len:
                    cut = view_len - max_len
                    rendered = self._cut_line(rendered, cut)

            if view_len - cut < self._fill:
                self.finish()

            self._output.write(rendered)
            if one_line and self.isatty():
                self._output.write("\r")
                self._fill = view_len - cut
            elif not no_nl:
                self._output.write("\n")
                self._fill = 0
            self._output.flush()

    def progress(self, iterable, wip, finish, length=20, refresh=0.1):
        if self.isatty():
            def print_pb(value, limit):
                (pb, pb_placeholders) = fmt.format_progress_bar(value, limit, length)
                if value < limit:
                    self.info("{} :: {}".format(pb, wip[0]), pb_placeholders + wip[1], one_line=True)
                else:
                    self.info("{} :: {}".format(pb, finish[0]), pb_placeholders + finish[1])

            current = 0
            stop_pb_thread = threading.Event()

            print_pb(0, 1)
            items = list(iterable)

            def refresh_pb():
                print_pb(current, len(items))
                while not stop_pb_thread.wait(refresh):
                    print_pb(current, len(items))
                print_pb(current, len(items))

            pb_thread = threading.Thread(target=refresh_pb)
            pb_thread.daemon = True
            pb_thread.start()

            for (current, item) in enumerate(items, 1):
                yield item

            stop_pb_thread.set()
        else:
            yield from iterable

    def finish(self):
        if self._fill:
            self._output.write((" " * self._fill) + "\r")
            self._fill = 0
            self._output.flush()

    def _get_term_width(self):
        try:
            return int(os.environ["COLUMNS"])
        except (KeyError, ValueError):
            try:
                return os.get_terminal_size(self._output.fileno()).columns
            except OSError:
                return None

    def _format_text(self, text, placeholders, colored):
        text = text.format(**(_COLORS if colored else _NO_COLORS))
        text = text % tuple(
            (placeholder() if callable(placeholder) else placeholder)
            for placeholder in placeholders
        )
        return text

    def _cut_line(self, text, cut):
        parts = self._ansi_regexp.split(text)
        for index in reversed(range(len(parts))):
            if cut <= 0:
                break
            if parts[index].startswith("\x1b"):
                parts[index] = ""
            elif cut <= len(parts[index]):
                parts[index] = parts[index][:-cut]
                break
            else:
                cut -= len(parts[index])
                parts[index] = ""
        if self._colored:
            parts.append(Fore.RESET)
        return "".join(parts)
