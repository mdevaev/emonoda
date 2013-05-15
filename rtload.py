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
from rtlib import clients

import sys
import os
import errno
import socket
import argparse


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

	fake_path = os.path.join(data_dir_path, torrent.name())
	unlink_flag = False
	if not os.path.exists(fake_path) :
		open(fake_path, "w").close()
		unlink_flag = True
	os.symlink(fake_path, link_to_path)
	if unlink_flag :
		os.unlink(fake_path)


###
def loadTorrent(client, torrents_list, data_dir_path, link_to_path, mkdir_mode, customs_dict) :
	torrents_list = [ tfile.Torrent(os.path.abspath(item)) for item in torrents_list ]
	hashes_list = client.hashes()
	for torrent in torrents_list :
		if torrent.hash() in hashes_list :
			raise RuntimeError("%s: already loaded" % (torrent.path()))

	if data_dir_path is None :
		data_dir_path = client.defaultDataPrefix()

	for torrent in torrents_list :
		torrent_hash = torrent.hash()
		data_dir_path = os.path.join(data_dir_path, torrent_hash[0], torrent_hash)
		makeDirsTree(data_dir_path, mkdir_mode)

		if not link_to_path is None :
			linkData(torrent, data_dir_path, link_to_path, mkdir_mode)

		client.loadTorrent(torrent, data_dir_path)
		client.setCustoms(torrent, customs_dict)


##### Main #####
def main() :
	cli_parser = argparse.ArgumentParser(description="Add torrent in the data model \"rthash\"")
	cli_parser.add_argument("-d", "--data-dir",    dest="data_dir_path",    action="store", default=None, metavar="<path>")
	cli_parser.add_argument("-l", "--link-to",     dest="link_to_path",     action="store", default=None, metavar="<path>")
	cli_parser.add_argument("-t", "--timeout",     dest="socket_timeout",   action="store", default=5, type=int, metavar="<seconds>")
	cli_parser.add_argument("-m", "--mkdir-mode",  dest="mkdir_mode",       action="store", default=None, type=int, metavar="<mode>")
	cli_parser.add_argument(      "--client",      dest="client_name",      action="store", required=True, choices=clients.CLIENTS_MAP.keys(), metavar="<plugin>")
	cli_parser.add_argument(      "--client-url",  dest="client_url",       action="store", default=None, metavar="<url>")
	cli_parser.add_argument(      "--set-customs", dest="set_customs_list", nargs="+",      default=None, metavar="<key(=value)>")
	cli_parser.add_argument("torrents_list", type=str, nargs="+")
	cli_options = cli_parser.parse_args(sys.argv[1:])

	if len(cli_options.torrents_list) > 1 and not cli_options.link_to_path is None :
		print >> sys.stderr, "Option -l/--link-to be used with only one torrent"
		sys.exit(1)

	if not cli_options.mkdir_mode is None :
		cli_options.mkdir_mode = int(str(cli_options.mkdir_mode), 8)

	socket.setdefaulttimeout(cli_options.socket_timeout)

	client_class = clients.CLIENTS_MAP[cli_options.client_name]
	client = client_class(cli_options.client_url)

	customs_dict = {}
	if not cli_options.set_customs_list is None :
		valid_keys_list = client.customKeys()
		for pair in cli_options.set_customs_list :
			(key, value) = map(str.strip, (pair.split("=", 1)+[""])[:2])
			if not key in valid_keys_list :
				print >> sys.stderr, "Invalid custom key: %s" % (key or "<empty>")
				sys.exit(1)
			customs_dict[key] = value

	loadTorrent(client,
		cli_options.torrents_list,
		cli_options.data_dir_path,
		cli_options.link_to_path,
		cli_options.mkdir_mode,
		customs_dict,
	)


###
if __name__ == "__main__" :
	main()

