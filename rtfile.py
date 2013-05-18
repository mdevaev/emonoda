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
from rtlib import clientlib

from rtlib import tools
import rtlib.tools.fmt # pylint: disable=W0611
import rtlib.tools.fs

import sys
import socket
import operator
import itertools
import datetime
import argparse


##### Public methods #####
def makeFilesList(files_dict, depth = 0, prefix = "\t") :
	text = ""
	for (key, value_dict) in sorted(files_dict.iteritems(), key=operator.itemgetter(0)) :
		text += prefix + "*   " * depth + key + "\n"
		text += makeFilesList(value_dict, depth + 1)
	return text


###
def formatSize(torrent) :
	return tools.fmt.formatSize(torrent.size())

def formatAnnounce(torrent) :
	return ( torrent.announce() or "" )

def formatAnnounceListPretty(torrent) :
	return " ".join(itertools.chain.from_iterable(torrent.announceList()))

def formatCreationDatePretty(torrent) :
	return ( datetime.datetime.utcfromtimestamp(torrent.creationDate()) if not torrent.creationDate() is None else "" )

def formatCreatedBy(torrent) :
	return ( torrent.createdBy() or "" )

def formatComment(torrent) :
	return ( torrent.comment() or "" )

def formatClientPath(torrent, client) :
	try :
		return client.dataPrefix(torrent)
	except clientlib.NoSuchTorrentError :
		return ""

def formatFilesList(torrent) :
	return makeFilesList(tools.fs.treeListToDict(torrent.files()))

def printPrettyMeta(torrent, client) :
	print "Torrent:       ", torrent.path()
	print "Name:          ", torrent.name()
	print "Hash:          ", torrent.hash()
	print "Size:          ", formatSize(torrent)
	print "Announce:      ", formatAnnounce(torrent)
	print "Announce list: ", formatAnnounceListPretty(torrent)
	print "Creation date: ", formatCreationDatePretty(torrent)
	print "Created by:    ", formatCreatedBy(torrent)
	print "Comment:       ", formatComment(torrent)
	if not client is None :
		print "Client path:   ", formatClientPath(torrent, client)
	if torrent.isSingleFile() :
		print "Provides:      ", tuple(torrent.files())[0]
	else :
		print "Provides:\n%s" % (formatFilesList(torrent))


##### Main #####
def main() :
	cli_parser = argparse.ArgumentParser(description="Show torrents metadata")
	cli_parser.add_argument(      "--name",        dest="print_name_flag",        action="store_true", default=False)
	cli_parser.add_argument(      "--hash",        dest="print_hash_flag",        action="store_true", default=False)
	cli_parser.add_argument(      "--comment",     dest="print_comment_flag",     action="store_true", default=False)
	cli_parser.add_argument(      "--size",        dest="print_size_flag",        action="store_true", default=False)
	cli_parser.add_argument(      "--size-pretty", dest="print_size_pretty_flag", action="store_true", default=False)
	cli_parser.add_argument(      "--announce",             dest="print_announce_flag",             action="store_true", default=False)
	cli_parser.add_argument(      "--announce-list",        dest="print_announce_list_flag",        action="store_true", default=False)
	cli_parser.add_argument(      "--creation-date",        dest="print_creation_date_flag",        action="store_true", default=False)
	cli_parser.add_argument(      "--creation-date-pretty", dest="print_creation_date_pretty_flag", action="store_true", default=False)
	cli_parser.add_argument(      "--created-by",           dest="print_created_by_flag",           action="store_true", default=False)
	cli_parser.add_argument(      "--provides",    dest="print_provides_flag",    action="store_true", default=False)
	cli_parser.add_argument(      "--client-path", dest="print_client_path_flag", action="store_true", default=False)
	cli_parser.add_argument(      "--make-magnet", dest="print_magnet_flag",      action="store_true", default=False)
	cli_parser.add_argument(      "--magnet-fields", dest="magnet_fields_list",   nargs="+", default=None, metavar="<fields>", choices=("dn", "tr"))
	cli_parser.add_argument("-t", "--timeout",     dest="socket_timeout", action="store", default=5, type=int, metavar="<seconds>")
	cli_parser.add_argument(      "--client",      dest="client_name",    action="store", default=None, choices=clients.CLIENTS_MAP.keys(), metavar="<plugin>")
	cli_parser.add_argument(      "--client-url",  dest="client_url",     action="store", default=None, metavar="<url>")
	cli_parser.add_argument("torrents_list", type=str, nargs="+")
	cli_options = cli_parser.parse_args(sys.argv[1:])

	socket.setdefaulttimeout(cli_options.socket_timeout)

	torrents_list = [ tfile.Torrent(item) for item in cli_options.torrents_list ]

	client = None
	if not cli_options.client_name is None :
		client_class = clients.CLIENTS_MAP[cli_options.client_name]
		client = client_class(cli_options.client_url)

	for torrent in torrents_list :
		if cli_options.print_name_flag :
			print torrent.name()
		elif cli_options.print_hash_flag :
			print torrent.hash()
		elif cli_options.print_size_flag :
			print torrent.size()
		elif cli_options.print_size_pretty_flag :
			print formatSize(torrent)
		elif cli_options.print_announce_flag :
			print formatAnnounce(torrent)
		elif cli_options.print_announce_list_flag :
			print formatAnnounceListPretty(torrent)
		elif cli_options.print_creation_date_flag :
			print ( torrent.creationDate() or "" )
		elif cli_options.print_creation_date_pretty_flag :
			print formatCreationDatePretty(torrent)
		elif cli_options.print_created_by_flag :
			print formatCreatedBy(torrent)
		elif cli_options.print_comment_flag :
			print formatComment(torrent)
		elif cli_options.print_provides_flag :
			for file_path in sorted(torrent.files()) :
				print file_path
		elif cli_options.print_client_path_flag :
			assert not client is None, "Required client"
			print formatClientPath(torrent, client)
		elif cli_options.print_magnet_flag :
			print torrent.magnet(cli_options.magnet_fields_list)
		else :
			printPrettyMeta(torrent, client)
			if len(torrents_list) > 1 :
				print


###
if __name__ == "__main__" :
	main()

