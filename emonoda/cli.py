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
import time

from enum import Enum

from typing import TextIO
from typing import Tuple
from typing import List
from typing import NamedTuple
from typing import Iterable
from typing import Generator
from typing import Optional
from typing import Any

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
class CellAlign(Enum):
    LEFT = "ljust"
    RIGHT = "rjust"
    CENTER = "center"


class Cell(NamedTuple):
    data: str
    colors: str = ""  # {red}
    align: CellAlign = CellAlign.LEFT


class Log:
    def __init__(
        self,
        use_colors: bool=True,
        force_colors: bool=False,
        quiet: bool=False,
        output: TextIO=sys.stdout,
    ) -> None:

        self.__quiet = quiet
        self.__output = output
        self.__fill = 0
        self.__colored = (use_colors and (self.isatty() or force_colors))
        self.__ansi_regexp = re.compile(r"(\x1b[^m]*m)")

    def isatty(self) -> bool:
        return self.__output.isatty()

    def info(self, text: str, placeholders: Tuple=(), one_line: bool=False, no_nl: bool=False) -> None:
        self.print("# {green}I{reset}: " + text, placeholders, one_line, no_nl)

    def error(self, text: str, placeholders: Tuple=(), one_line: bool=False, no_nl: bool=False) -> None:
        self.print("# {red}E{reset}: " + text, placeholders, one_line, no_nl)

    def print(self, text: str="", placeholders: Tuple=(), one_line: bool=False, no_nl: bool=False) -> None:
        if not self.__quiet:
            rendered = self.__format_text(text, placeholders, self.__colored)
            view_len = len(self.__format_text(text, placeholders, False) if self.__colored else rendered)

            cut = 0
            if one_line and self.isatty():
                max_len = self.__get_term_width()
                if max_len is not None and view_len > max_len:
                    cut = view_len - max_len
                    rendered = self.__cut_line(rendered, cut)

            if view_len - cut < self.__fill:
                self.finish()

            self.__output.write(rendered)
            if one_line and self.isatty():
                self.__output.write("\r")
                self.__fill = view_len - cut
            elif not no_nl:
                self.__output.write("\n")
                self.__fill = 0
            self.__output.flush()

    def print_table(self, header: List[Cell], table: List[List[Cell]]) -> None:
        assert len(header) >= 1
        widths = [len(cell.data) for cell in header]
        for row in table:
            for (cell_index, cell) in enumerate(row):
                if len(cell.data) > widths[cell_index]:
                    widths[cell_index] = len(cell.data)

        text_rows: List[str] = []
        for (row_index, row) in enumerate([header] + table):
            text_cells: List[str] = []
            for (cell_index, cell) in enumerate(row):
                text_cells.append(
                    cell.colors
                    + getattr(cell.data, cell.align.value)(widths[cell_index])
                    + ("{reset}" if cell.colors else "")
                )
            text_rows.append(" " + " | ".join(text_cells))

            if row_index == 0:
                text_rows.append("=" + "+".join(
                    "=" * (width + (2 if 0 < width_index < len(widths) else 1))
                    for (width_index, width) in enumerate(widths)
                ))

        self.print("\n".join(text_rows))

    def progress(
        self,
        iterable: Iterable[Any],
        wip: Tuple[str, Tuple],
        finish: Tuple[str, Tuple],
        length: int=20,
        refresh: float=0.1,
    ) -> Generator[Any, None, None]:

        if self.isatty():
            items = list(iterable)

            current = 0
            prev = 0.0
            for (current, item) in enumerate(items, 1):
                now = time.time()
                if prev + refresh < now:
                    (pb, pb_placeholders) = fmt.format_progress_bar(current, len(items), length)
                    self.info("{} :: {}".format(pb, wip[0]), pb_placeholders + wip[1], one_line=True)
                    prev = now
                yield item

            (pb, pb_placeholders) = fmt.format_progress_bar(current, len(items), length)
            self.info("{} :: {}".format(pb, finish[0]), pb_placeholders + finish[1])

        else:
            yield from iterable

    def finish(self) -> None:
        if self.__fill:
            self.__output.write((" " * self.__fill) + "\r")
            self.__fill = 0
            self.__output.flush()

    def __get_term_width(self) -> Optional[int]:
        try:
            return int(os.environ["COLUMNS"])
        except (KeyError, ValueError):
            try:
                return os.get_terminal_size(self.__output.fileno()).columns
            except OSError:
                return None

    def __format_text(self, text: str, placeholders: Tuple, colored: bool) -> str:
        text = text.format(**(_COLORS if colored else _NO_COLORS))
        text = text % tuple(
            (placeholder() if callable(placeholder) else placeholder)
            for placeholder in placeholders
        )
        return text

    def __cut_line(self, text: str, cut: int) -> str:
        parts = self.__ansi_regexp.split(text)
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
        if self.__colored:
            parts.append(Fore.RESET)
        return "".join(parts)
