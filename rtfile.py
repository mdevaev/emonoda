#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
#
#    rtfile -- Show torrents metadata
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


from rtlib import tfile
from rtlib import clients

from rtlib import tools
import rtlib.tools.fmt # pylint: disable=W0611
import rtlib.tools.fs

import sys
import socket
import operator
import argparse


##### Public methods #####
def printFilesDict(files_dict, depth = 0, prefix="\t") :
	for (key, value_dict) in sorted(files_dict.iteritems(), key=operator.itemgetter(0)) :
		print prefix + "*   " * depth + key
		printFilesDict(value_dict, depth + 1)

def printPrettyMeta(client, torrents_list) :
	torrents_list = [ tfile.Torrent(item) for item in torrents_list ]
	hashes_list = ( client.hashes() if not client is None else None )

	for torrent in torrents_list :
		print "Torrent:     ", torrent.path()
		print "Name:        ", torrent.name()
		print "Hash:        ", torrent.hash()
		print "Comment:     ", torrent.comment()
		print "Size:        ", tools.fmt.formatSize(torrent.size())
		if not client is None :
			print "Client path: ", ( client.dataPrefix(torrent) if torrent.hash() in hashes_list else "" )
		if torrent.isSingleFile() :
			print "Provides:    ", tuple(torrent.files())[0]
		else :
			print "Provides:"
			printFilesDict(tools.fs.treeListToDict(torrent.files()))


##### Main #####
def main() :
	cli_parser = argparse.ArgumentParser(description="Show torrents metadata")
	cli_parser.add_argument(      "--name",        dest="print_name_flag",        action="store_true", default=False)
	cli_parser.add_argument(      "--hash",        dest="print_hash_flag",        action="store_true", default=False)
	cli_parser.add_argument(      "--comment",     dest="print_comment_flag",     action="store_true", default=False)
	cli_parser.add_argument(      "--size",        dest="print_size_flag",        action="store_true", default=False)
	cli_parser.add_argument(      "--size-pretty", dest="print_size_pretty_flag", action="store_true", default=False)
	cli_parser.add_argument(      "--provides",    dest="print_provides_flag",    action="store_true", default=False)
	cli_parser.add_argument(      "--client-path", dest="print_client_path_flag", action="store_true", default=False)
	cli_parser.add_argument("-t", "--timeout",     dest="socket_timeout", action="store", default=5, type=int, metavar="<seconds>")
	cli_parser.add_argument(      "--client",      dest="client_name",    action="store", default=None, choices=clients.CLIENTS_MAP.keys(), metavar="<plugin>")
	cli_parser.add_argument(      "--client-url",  dest="client_url",     action="store", default=None, metavar="<url>")
	cli_parser.add_argument("torrents_list", type=str, nargs="+")
	cli_options = cli_parser.parse_args(sys.argv[1:])

	socket.setdefaulttimeout(cli_options.socket_timeout)

	client = None
	if not cli_options.client_name is None :
		client_class = clients.CLIENTS_MAP[cli_options.client_name]
		client = client_class(cli_options.client_url)

	torrent = tfile.Torrent(cli_options.torrents_list[0])
	if cli_options.print_name_flag :
		print torrent.name()
	elif cli_options.print_hash_flag :
		print torrent.hash()
	elif cli_options.print_comment_flag :
		print torrent.comment()
	elif cli_options.print_size_flag :
		print torrent.size()
	elif cli_options.print_size_pretty_flag :
		print tools.fmt.formatSize(torrent.size())
	elif cli_options.print_provides_flag :
		for file_path in sorted(torrent.files()) :
			print file_path
	elif cli_options.print_client_path_flag :
		assert not client is None, "Required client"
		print ( client.dataPrefix(torrent) if torrent.hash() in client.hashes() else "" )
	else :
		printPrettyMeta(client, cli_options.torrents_list)


###
if __name__ == "__main__" :
	main()

