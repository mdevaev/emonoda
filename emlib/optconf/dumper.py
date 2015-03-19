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


import json
import operator

import colorama
import pygments
import pygments.lexers
import pygments.formatters

from ..thirdparty.tabloid import FormattedTable

from . import Section


# =====
def make_config_dump(config, split_by, width=None):
    table = FormattedTable(width=width, header_background=colorama.Back.BLUE)
    table.add_column("Option", _format_option)
    table.add_column("Value", _format_value)
    table.add_column("Default", _format_default_value)
    table.add_column("Help")

    for row in _make_plain_dump(config, tuple(map(tuple, split_by))):
        if row is None:
            table.add_row((" ") * 4)
        else:
            table.add_row(row)
    return "\n".join(table.get_table())


def _format_option(name, row):
    if row[1] != row[2]:
        return "{}{}{}".format(colorama.Fore.RED, name, colorama.Style.RESET_ALL)
    return name


def _format_value(value, _):
    return pygments.highlight(
        value,
        pygments.lexers.PythonLexer(),
        pygments.formatters.TerminalFormatter(bg="dark"),
    ).replace("\n", "")


def _format_default_value(value, row):
    if row[1] != row[2]:
        return _format_value(value, None)
    else:
        return " " * len(value)


def _make_plain_dump(config, split_by=(), path=()):
    plain = []
    for (key, value) in sorted(config.items(), key=operator.itemgetter(0)):
        if isinstance(value, Section):
            if len(plain) != 0 and path in split_by:
                plain.append(None)
            plain += _make_plain_dump(value, split_by, path + (key,))
        else:
            default = config._get_default(key)  # pylint: disable=protected-access
            plain.append((
                "/".join(path + (key,)),
                json.dumps(value),
                json.dumps(default),
                config._get_help(key),  # pylint: disable=protected-access
            ))
    return plain
