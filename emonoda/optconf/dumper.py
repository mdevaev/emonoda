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


# pylint: skip-file
# infinite recursion

import operator

from typing import Tuple
from typing import List
from typing import Any

import yaml

from . import Section


# =====
def make_config_dump(config: Section) -> str:
    return "\n".join(_inner_make_dump(config))


def _inner_make_dump(config: Section, _path: Tuple[str, ...]=()) -> List[str]:
    lines = []
    for (key, value) in sorted(config.items(), key=operator.itemgetter(0)):
        indent = len(_path) * "    "
        if isinstance(value, Section):
            lines.append("{}{}:".format(indent, key))
            lines += _inner_make_dump(value, _path + (key,))
            lines.append("")
        else:
            default = config._get_default(key)  # pylint: disable=protected-access
            comment = config._get_help(key)  # pylint: disable=protected-access
            print_value = (None if config._is_secret(key) else value)  # pylint: disable=protected-access
            if default == value:
                lines.append("{}{}: {} # {}".format(indent, key, _make_yaml(print_value), comment))
            else:
                lines.append("{}# {}: {} # {}".format(indent, key, _make_yaml(default), comment))
                if config._is_secret(key):
                    lines.append("{}# Note: value is secret and has been hidden".format(indent))
                lines.append("{}{}: {}".format(indent, key, _make_yaml(print_value)))
    return lines


def _make_yaml(value: Any) -> str:
    return yaml.dump(value, allow_unicode=True).replace("\n...\n", "").strip()
