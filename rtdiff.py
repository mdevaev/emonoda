#!/usr/bin/env python3
#
#    rtfile -- Show the difference between two torrent files.
#    Copyright (C) 2013  Devaev Maxim <mdevaev@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#####


import re
import os
import socket

from rtlib import tfile
from rtlib import clients
from rtlib import config


##### Main #####
def main() :
    parser = config.makeParser(description="Show the difference between two torrent files")
    parser.addArguments(
        config.ARG_TIMEOUT,
        config.ARG_CLIENT,
        config.ARG_CLIENT_URL,
        config.ARG_NO_COLORS,
        config.ARG_USE_COLORS,
        config.ARG_FORCE_COLORS,
        config.ARG_NO_FORCE_COLORS,
    )
    parser.addRawArgument("torrents_list", type=str, nargs=2, metavar="<path/hash>")
    options = parser.sync((config.SECTION_MAIN, config.SECTION_RTDIFF))[0]

    socket.setdefaulttimeout(options.timeout)

    client = None
    if options.client_name is not None :
        client_class = clients.CLIENTS_MAP[options.client_name]
        client = client_class(options.client_url)

    hash_regexp = re.compile(r"[\da-fA-F]{40}")
    for count in range(2) :
        item = options.torrents_list[count]
        if os.path.exists(item) :
            options.torrents_list[count] = tfile.Torrent(item).files()
        elif hash_regexp.match(item) :
            if client is None :
                raise RuntimeError("Required client for hash: %s" % (item))
            options.torrents_list[count] = client.files(item)
        else :
            raise RuntimeError("Invalid file or hash: %s" % (item))

    tfile.printDiff(tfile.diff(*options.torrents_list), " ",
        use_colors_flag=(not options.no_colors_flag),
        force_colors_flag=options.force_colors_flag,
    )


###
if __name__ == "__main__" :
    main()

