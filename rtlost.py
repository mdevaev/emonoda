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

import sys
import os
import argparse


##### Public methods #####
def torrentsProvides(src_dir_path, data_dir_path) :
	data_files_list = []
	for torrent in tfile.torrents(src_dir_path).values() :
		for file_path in torrent.files(data_dir_path) :
			data_files_list.append(file_path)
	return data_files_list

def onWalkError(exception) :
	raise exception

def dataProvides(data_dir_path) :
	data_files_list = []
	for (root, dirs_list, files_list) in os.walk(data_dir_path, onerror=onWalkError) :
		for item in dirs_list + files_list :
			data_files_list.append(os.path.join(root, item))
	return data_files_list

def searchLost(src_dir_path, data_dir_path) :
	data_dir_path = os.path.abspath(data_dir_path)
	torrents_tree_set = set(torrentsProvides(src_dir_path, data_dir_path))
	data_tree_set = set(dataProvides(data_dir_path))
	for file_path in sorted(data_tree_set.difference(torrents_tree_set)) :
		print file_path


###
def requiredOptions(main_action, options, actions_list) :
	errors_list = []
	for action in actions_list :
		if getattr(options, action.dest) is None :
			errors_list.append("/".join(action.option_strings))
	if len(errors_list) != 0 :
		print "%s: these arguments are required for %s" % (os.path.basename(sys.argv[0]), "/".join(main_action.option_strings))
		for error in errors_list :
			print "\t" + error
		sys.exit(1)


##### Main #####
def main() :
	cli_parser = argparse.ArgumentParser(description="Shows a list of files in the specified directory, not registered in rtorrent")
	modes_group = cli_parser.add_mutually_exclusive_group(required=True)
	lost_files_opt =    modes_group.add_argument("--lost-files",    dest="lost_files_flag",    action="store_true", default=False)

	src_dir_opt =  cli_parser.add_argument("-s", "--source-dir", dest="src_dir_path",  action="store", metavar="<dir>")
	data_dir_opt = cli_parser.add_argument("-d", "--data-dir",   dest="data_dir_path", action="store", metavar="<dir>")

	cli_options = cli_parser.parse_args(sys.argv[1:])
	if cli_options.lost_files_flag :
		requiredOptions(lost_files_opt, cli_options, (src_dir_opt, data_dir_opt))
		searchLost(
			cli_options.src_dir_path,
			cli_options.data_dir_path,
		)


###
if __name__ == "__main__" :
	main()

