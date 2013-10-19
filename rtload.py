#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
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


from rtlib import tfile
from rtlib import clientlib
from rtlib import clients
from rtlib import config

import sys
import os
import errno
import socket


##### Public classes #####
def makeDirsTree(path, last_mode) :
	try :
		os.makedirs(path)
		os.chmod(path, last_mode)
	except OSError, err :
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

def loadTorrent(client, src_dir_path, torrents_list, data_dir_path, link_to_path, mkdir_mode, customs_dict) :
	torrents_list = [
		tfile.Torrent( os.path.abspath(item) if src_dir_path == "." else os.path.join(src_dir_path, item) )
		for item in torrents_list
	]
	for torrent in torrents_list :
		if client.hasTorrent(torrent) :
			raise RuntimeError("%s: already loaded" % (torrent.path()))

	if data_dir_path is None :
		data_dir_path = client.defaultDataPrefix()

	for torrent in torrents_list :
		base_dir_name = os.path.basename(torrent.path()) + ".data"
		base_dir_path = os.path.join(data_dir_path, base_dir_name[0], base_dir_name)
		makeDirsTree(base_dir_path, mkdir_mode)

		if not link_to_path is None :
			linkData(torrent, base_dir_path, link_to_path, mkdir_mode)

		client.loadTorrent(torrent, base_dir_path)
		if len(customs_dict) != 0 :
			client.setCustoms(torrent, customs_dict)


##### Main #####
def main() :
	(cli_parser, config_dict, argv_list) = config.partialParser(sys.argv[1:], description="Add torrent to the data model \"t.data\"")
	config.addArguments(cli_parser,
		config.ARG_MKDIR_MODE,
		config.ARG_DATA_DIR,
		config.ARG_SOURCE_DIR,
		config.ARG_TIMEOUT,
		config.ARG_CLIENT,
		config.ARG_CLIENT_URL,
		config.ARG_SET_CUSTOMS,
	)
	cli_parser.add_argument("--link-to", dest="link_to_path", action="store", default=None, metavar="<path>")
	cli_parser.add_argument("torrents_list", type=str, nargs="+")
	cli_options = cli_parser.parse_args(argv_list)
	config.syncParsers(config.SECTION_RTLOAD, cli_options, config_dict)

	if len(cli_options.torrents_list) > 1 and not cli_options.link_to_path is None :
		print >> sys.stderr, "Option -l/--link-to be used with only one torrent"
		sys.exit(1)
	if cli_options.client_name is None :
		print >> sys.stderr, "Required client"
		sys.exit(1)

	socket.setdefaulttimeout(cli_options.socket_timeout)

	client = clientlib.initClient(
		clients.CLIENTS_MAP[cli_options.client_name],
		cli_options.client_url,
		set_customs_dict=cli_options.set_customs_dict
	)

	loadTorrent(client,
		cli_options.src_dir_path,
		cli_options.torrents_list,
		cli_options.data_dir_path,
		cli_options.link_to_path,
		cli_options.mkdir_mode,
		cli_options.set_customs_dict,
	)


###
if __name__ == "__main__" :
	main()

