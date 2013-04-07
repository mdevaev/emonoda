#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
#
#    rtlost -- Shows a list of files in the specified directory, not registered in rtorrent
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
from rtlib import rtapi

import sys
import os
import argparse


##### Public methods #####
def torrentProvides(torrent, prefix = "") :
	# XXX: See https://wiki.theory.org/BitTorrentSpecification for details
	bencode_dict = torrent.bencode()
	base = os.path.join(prefix, bencode_dict["info"]["name"])
	if not bencode_dict["info"].has_key("files") : # Single File Mode
		return [base]
	else : # Multiple File Mode
		files_list = [base]
		for file_dict in bencode_dict["info"]["files"] :
			for (index, _) in enumerate(file_dict["path"]) :
				files_list.append(os.path.join(prefix, base, os.path.sep.join(file_dict["path"][0:index + 1])))
		return files_list

def onError(exception) :
	raise exception

def dataProvides(data_dir_path) :
	data_files_list = []
	for (root, dirs_list, files_list) in os.walk(data_dir_path, onerror=onError) :
		for item in dirs_list + files_list :
			data_files_list.append(os.path.join(root, item))
	return data_files_list

def searchLost(interface, torrents_dir_path, data_dir_path) :
	data_dir_path = os.path.abspath(data_dir_path)

	torrents_tree_set = set()
	for torrent in tfile.torrents(torrents_dir_path).values() :
		for file_path in torrentProvides(torrent, data_dir_path) :
			torrents_tree_set.add(file_path)

	data_tree_set = set(dataProvides(data_dir_path))

	for file_path in sorted(data_tree_set.difference(torrents_tree_set)) :
		print file_path


##### Main #####
def main() :
	cli_parser = argparse.ArgumentParser(description="Shows a list of files in the specified directory, not registered in rtorrent")
	cli_parser.add_argument("-t", "--torrents-dir", dest="torrents_dir_path", action="store", required=True, metavar="<dir>")
	cli_parser.add_argument("-d", "--data-dir",     dest="data_dir_path",     action="store", required=True, metavar="<dir>")
	cli_options = cli_parser.parse_args(sys.argv[1:])

	searchLost(
		cli_options.torrents_dir_path,
		cli_options.data_dir_path,
	)


###
if __name__ == "__main__" :
	main()

