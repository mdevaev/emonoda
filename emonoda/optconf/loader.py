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


import os

from typing import IO
from typing import Any

import yaml
import yaml.loader
import yaml.nodes


# =====
def load_file(file_path: str) -> Any:
    with open(file_path) as yaml_file:
        try:
            return yaml.load(yaml_file, _YamlLoader)
        except Exception:
            # Reraise internal exception as standard ValueError and show the incorrect file
            raise ValueError("Incorrect YAML syntax in file '{}'".format(file_path))


# =====
class _YamlLoader(yaml.loader.Loader):  # pylint: disable=too-many-ancestors
    def __init__(self, yaml_file: IO) -> None:
        yaml.loader.Loader.__init__(self, yaml_file)
        self.__root = os.path.dirname(yaml_file.name)

    def include(self, node: yaml.nodes.Node) -> str:
        # Logger which supports include-files
        file_path = os.path.join(self.__root, self.construct_scalar(node))  # pylint: disable=no-member
        return load_file(file_path)


_YamlLoader.add_constructor("!include", _YamlLoader.include)  # pylint: disable=no-member
