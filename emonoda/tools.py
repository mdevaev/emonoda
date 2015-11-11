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


# =====
def sorted_paths(paths, get=None):
    return sorted(paths, key=_make_get_path_nulled(get))


# =====
def _make_get_path_nulled(get):
    if get is None:
        def get_path_nulled(path):
            return path.replace(os.path.sep, "\0")
    else:
        def get_path_nulled(item):
            return item[get].replace(os.path.sep, "\0")
    return get_path_nulled
