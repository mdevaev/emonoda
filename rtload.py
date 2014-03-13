#!/usr/bin/env python3
#
#    rtfetch -- Update rtorrent files from popular trackers
#    Copyright (C) 2012  Devaev Maxim <mdevaev@gmail.com>
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


import sys
import os
import errno
import socket

from rtlib import tfile
from rtlib import clientlib
from rtlib import clients
from rtlib import config


##### Public classes #####
def makeDirsTree(path, last_mode) :
    try :
        os.makedirs(path)
        if last_mode is not None :
            os.chmod(path, last_mode)
    except OSError as err :
        if err.errno != errno.EEXIST :
            raise

def linkData(torrent, data_dir_path, link_to_path, mkdir_mode) :
    mkdir_path = link_to_path = os.path.abspath(link_to_path)
    if torrent.isSingleFile() :
        link_to_path = os.path.join(link_to_path, torrent.name())
    else :
        mkdir_path = os.path.dirname(link_to_path)

    if os.path.exists(link_to_path) :
        raise RuntimeError("%s: link target already exists" % (link_to_path))

    makeDirsTree(mkdir_path, mkdir_mode)
    os.symlink(os.path.join(data_dir_path, torrent.name()), link_to_path)

def loadTorrent(client, src_dir_path, torrents_list, data_dir_path, link_to_path, pre_mode, mkdir_mode, customs_dict) :
    torrents_list = [
        tfile.Torrent( os.path.abspath(item) if src_dir_path == "." else os.path.join(src_dir_path, item) )
        for item in torrents_list
    ]
    for torrent in torrents_list :
        if client.hasTorrent(torrent) :
            raise RuntimeError("%s: already loaded" % (torrent.path()))
        elif pre_mode is not None :
            os.chmod(torrent.path(), pre_mode)

    if data_dir_path is None :
        data_dir_path = client.defaultDataPrefix()

    for torrent in torrents_list :
        base_dir_name = os.path.basename(torrent.path()) + ".data"
        base_dir_path = os.path.join(data_dir_path, base_dir_name[0], base_dir_name)
        makeDirsTree(base_dir_path, mkdir_mode)

        if link_to_path is not None :
            linkData(torrent, base_dir_path, link_to_path, mkdir_mode)

        client.loadTorrent(torrent, base_dir_path)
        if len(customs_dict) != 0 :
            client.setCustoms(torrent, customs_dict)


##### Main #####
def main() :
    parser = config.makeParser(description="Add torrent to the data model \"t.data\"")
    parser.addArguments(
        config.ARG_MKDIR_MODE,
        config.ARG_PRE_MODE,
        config.ARG_DATA_DIR,
        config.ARG_SOURCE_DIR,
        config.ARG_TIMEOUT,
        config.ARG_CLIENT,
        config.ARG_CLIENT_URL,
        config.ARG_SET_CUSTOMS,
    )
    parser.addRawArgument("--link-to", dest="link_to_path", action="store", default=None, metavar="<path>")
    parser.addRawArgument("torrents_list", type=str, nargs="+")
    options = parser.sync((config.SECTION_MAIN, config.SECTION_RTLOAD))[0]

    if len(options.torrents_list) > 1 and options.link_to_path is not None :
        print("Option -l/--link-to be used with only one torrent", file=sys.stderr)
        sys.exit(1)
    if options.client_name is None :
        print("Required client", file=sys.stderr)
        sys.exit(1)

    socket.setdefaulttimeout(options.timeout)

    client = clientlib.initClient(
        clients.CLIENTS_MAP[options.client_name],
        options.client_url,
        set_customs_dict=options.set_customs_dict
    )

    loadTorrent(client,
        options.src_dir_path,
        options.torrents_list,
        options.data_dir_path,
        options.link_to_path,
        options.pre_mode,
        options.mkdir_mode,
        options.set_customs_dict,
    )


###
if __name__ == "__main__" :
    main()

