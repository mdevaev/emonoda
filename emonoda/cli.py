"""
    Emonoda -- The set of tools to organize and manage of your torrents
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

from colorama import Fore
from colorama import Style


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
        self._use_colors = use_colors
        self._force_colors = force_colors
        self._quiet = quiet
        self._output = output

    def isatty(self):
        return self._output.isatty()

    def info(self, text, *args, **kwargs):
        self.print("# {green}I{reset}: " + text, *args, **kwargs)

    def error(self, text, *args, **kwargs):
        self.print("# {red}E{reset}: " + text, *args, **kwargs)

    def print(self, text="", placeholders=(), one_line=False, no_nl=False):
        if not self._quiet:
            colored = (self._use_colors and (self.isatty() or self._force_colors))
            _inner_print(text, placeholders, colored, one_line, no_nl, self._output)

    def finish(self):
        _inner_finish(self._output)


# =====
_next_ctl = ""


def _format_text(text, placeholders, colored):
    text = text.format(**(_COLORS if colored else _NO_COLORS))
    text = text % placeholders
    return text


def _inner_print(text, placeholders, colored, one_line, no_nl, output):
    global _next_ctl  # pylint: disable=global-statement
    output.write(_next_ctl + _format_text(text, placeholders, colored))
    output.flush()
    if no_nl:
        _next_ctl = ""
    else:
        stub_len = len(_format_text(text, placeholders, False))
        _next_ctl = ("\r" + (" " * stub_len) + "\r" if one_line else "\n")


def _inner_finish(output):
    global _next_ctl  # pylint: disable=global-statement
    if len(_next_ctl) != 0:
        output.write("\n")
        output.flush()
        _next_ctl = ""
