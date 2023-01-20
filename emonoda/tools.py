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

from typing import List
from typing import Sequence
from typing import Iterable
from typing import Optional
from typing import Any

import chardet


# =====
def make_sub_name(path: str, prefix: str, suffix: str) -> str:
    return os.path.join(
        os.path.dirname(path),
        prefix + os.path.basename(path) + suffix,
    )


def sorted_paths(paths: Iterable, get: Optional[Any]=None) -> List:
    if get is None:
        # def for speed
        def get_path_nulled(path: str) -> str:
            return path.replace(os.path.sep, "\0")
    else:
        def get_path_nulled(item: Sequence) -> str:  # type: ignore
            return item[get].replace(os.path.sep, "\0")  # type: ignore
    return sorted(paths, key=get_path_nulled)


def get_decoded_path(path: str) -> str:
    try:
        path.encode()
        return path
    except UnicodeEncodeError:
        path_bytes = os.fsencode(path)
        try:
            return path_bytes.decode("cp1251")
        except UnicodeDecodeError:
            encoding = chardet.detect(path_bytes)["encoding"]
            assert encoding is not None, f"Can't determine encoding for bytes string: {path_bytes!r}"
            return path_bytes.decode(encoding)
