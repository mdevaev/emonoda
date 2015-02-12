"""
    rtfetch -- The set of tools to organize and manage your torrents
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


from . import tfile
from . import fmt


# =====
def load_torrents_from_dir(dir_path, name_filter, log):
    if log.isatty():
        fan = fmt.make_fan()

        def load_torrent(path):
            log.print("# Caching {cyan}%s/{yellow}%s {magenta}%s{reset}" % (
                      dir_path, name_filter, next(fan)), one_line=True)
            return tfile.load_torrent_from_path(path)
    else:
        log.print("# Caching {cyan}%s/{yellow}%s ..." % (dir_path, name_filter))
        load_torrent = tfile.load_torrent_from_path

    torrents = tfile.load_from_dir(dir_path, name_filter, as_abs=True, loader=load_torrent)

    log.print("# Cached {magenta}%d{reset} torrents from {cyan}%s/{yellow}%s{reset}" % (
              len(torrents), dir_path, name_filter))
    return torrents
