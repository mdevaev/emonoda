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
        self._quiet = quiet
        self._output = output
        self._fill = 0
        self._colored = (use_colors and (self.isatty() or force_colors))

    def isatty(self):
        return self._output.isatty()

    def info(self, text, *args, **kwargs):
        self.print("# {green}I{reset}: " + text, *args, **kwargs)

    def error(self, text, *args, **kwargs):
        self.print("# {red}E{reset}: " + text, *args, **kwargs)

    def print(self, text="", placeholders=(), one_line=False, no_nl=False):
        if not self._quiet:
            self.finish()
            self._output.write(self._format_text(text, placeholders, self._colored))
            if one_line:
                self._output.write("\r")
                self._fill = len(self._format_text(text, placeholders, False))
            elif not no_nl:
                self._output.write("\n")
                self._fill = 0

    def finish(self):
        if self._fill:
            self._output.write((" " * self._fill) + "\r")
            self._fill = 0

    def _format_text(self, text, placeholders, colored):
        text = text.format(**(_COLORS if colored else _NO_COLORS))
        text = text % placeholders
        return text
