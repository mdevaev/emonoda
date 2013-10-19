#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
#
#    rtquery -- Tool for querying torrents
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
from rtlib import clientlib
from rtlib import fs
from rtlib import config

import sys
import os
import socket
import argparse


##### Public methods #####
def formatTorrent(client, torrent) :
	if not isinstance(torrent, tfile.Torrent) :
		(path, name) = (client.torrentPath(torrent) or "<Temporary not saved>", client.name(torrent))
	else :
		(path, name) = (torrent.path(), torrent.name())
	return "%s --- %s" % (path, name)


###
def querySearchLost(client, src_dir_path, data_dir_path) :
	data_dir_path = os.path.abspath(data_dir_path)
	if client != None :
		torrents_tree_set = set(clientlib.indexed(client, True))
	else :
		torrents_tree_set = set(tfile.indexed(src_dir_path, data_dir_path).keys())
	data_tree_set = set(fs.treeList(data_dir_path))
	for file_path in sorted(data_tree_set.difference(torrents_tree_set)) :
		print file_path

def queryWhatProvides(client, src_dir_path, data_dir_path, file_path) :
	data_dir_path = ( os.path.abspath(data_dir_path) if not data_dir_path is None else "" )
	system_path_flag = os.path.isabs(file_path)
	if not data_dir_path is None and not system_path_flag :
		file_path = os.path.join(data_dir_path, file_path)

	if client != None :
		files_dict = clientlib.indexed(client, system_path_flag)
	else :
		files_dict = tfile.indexed(src_dir_path, data_dir_path)

	if files_dict.has_key(file_path) :
		for torrent in files_dict[file_path] :
			print formatTorrent(client, torrent)

def queryConflicts(client, src_dir_path) :
	if client != None :
		files_dict = clientlib.indexed(client, True)
	else :
		files_dict = tfile.indexed(src_dir_path)
	for (full_path, torrents_set) in files_dict.iteritems() :
		if len(torrents_set) > 1 :
			print full_path
			for torrent in torrents_set :
				print "\t" + formatTorrent(client, torrent)


###
def requiredOptions(main_action, options, actions_list) :
	errors_list = []
	for action in actions_list :
		if not getattr(options, action.dest) :
			errors_list.append("/".join(action.option_strings))
	if len(errors_list) != 0 :
		print "%s: these arguments are required for %s" % (os.path.basename(sys.argv[0]), "/".join(main_action.option_strings))
		for error in errors_list :
			print "\t" + error
		sys.exit(1)


##### Main #####
def main() :
	cli_parser = argparse.ArgumentParser(description="Tool for querying torrents")
	queries_group = cli_parser.add_mutually_exclusive_group(required=True)
	client_group = cli_parser.add_mutually_exclusive_group(required=True)

	lost_files_opt    = queries_group.add_argument("--lost-files",    dest="lost_files_flag",    action="store_true", default=False)
	what_provides_opt = queries_group.add_argument("--what-provides", dest="what_provides_flag", action="store_true", default=False)
	conflicts_opt     = queries_group.add_argument("--conflicts",     dest="conflicts_flag",     action="store_true", default=False)

	src_dir_opt = client_group.add_argument("-s", "--source-dir", dest="src_dir_path",  action="store", metavar="<dir>")
	client_group.add_argument(                    "--client",     dest="client_name",   action="store", default=None, choices=clients.CLIENTS_MAP.keys(), metavar="<plugin>")

	data_dir_opt = cli_parser.add_argument("-d", "--data-dir",   dest="data_dir_path",  action="store", metavar="<dir>")
	file_opt     = cli_parser.add_argument("-f", "--file",       dest="file_path",      action="store", metavar="<file>")
	cli_parser.add_argument(               "-t", "--timeout",    dest="socket_timeout", action="store", default=config.DEFAULT_TIMEOUT, type=int, metavar="<seconds>")
	cli_parser.add_argument(                     "--client-url", dest="client_url",     action="store", default=None, metavar="<url>")

	cli_options = cli_parser.parse_args(sys.argv[1:])

	socket.setdefaulttimeout(cli_options.socket_timeout)
	client = None
	if not cli_options.client_name is None :
		client_class = clients.CLIENTS_MAP[cli_options.client_name]
		client = client_class(cli_options.client_url)

	if cli_options.lost_files_flag :
		requiredOptions(lost_files_opt, cli_options, (data_dir_opt,))
		querySearchLost(
			client,
			cli_options.src_dir_path,
			cli_options.data_dir_path,
		)
	elif cli_options.what_provides_flag :
		if client is None :
			requiredOptions(what_provides_opt, cli_options, (src_dir_opt, file_opt))
		else :
			requiredOptions(what_provides_opt, cli_options, (file_opt,))
		queryWhatProvides(
			client,
			cli_options.src_dir_path,
			cli_options.data_dir_path,
			cli_options.file_path,
		)
	elif cli_options.conflicts_flag :
		if client is None :
			requiredOptions(conflicts_opt, cli_options, (src_dir_opt,))
		queryConflicts(
			client,
			cli_options.src_dir_path,
		)


###
if __name__ == "__main__" :
	main()

