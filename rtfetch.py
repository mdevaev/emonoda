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
from rtlib import fetcherlib
from rtlib import fetchers
from rtlib import clients

from rtlib import tools
import rtlib.tools.cli # pylint: disable=W0611

import sys
import os
import socket
import errno
import traceback
import operator
import argparse
import ConfigParser
import shutil
import time


##### Public constants #####
DELIMITER = "-" * 10


##### Public methods #####
def downloadTorrent(torrent, fetcher) :
	torrent_data = fetcher.fetchTorrent(torrent)
	new_file_path = torrent.path() + ".new"
	with open(new_file_path, "w") as new_file :
		new_file.write(torrent_data)
	return new_file_path

def replaceTorrent(torrent, new_file_path) :
	try :
		os.remove(torrent.path())
	except OSError, err :
		if err.errno != errno.ENOENT :
			raise
	os.rename(new_file_path, torrent.path())
	torrent.reload()

def updateTorrent(torrent, fetcher, backup_dir_path, client, save_customs_list) :
	old_torrent = tfile.Torrent(torrent.path())

	new_file_path = downloadTorrent(torrent, fetcher)
	if not backup_dir_path is None :
		backup_file_path = os.path.join(backup_dir_path, "%s.%d.bak" % (os.path.basename(torrent.path()), time.time()))
		shutil.copyfile(torrent.path(), backup_file_path)

	if not client is None :
		client.removeTorrent(torrent)
		customs_dict = dict([ (key, client.custom(key, torrent)) for key in save_customs_list ])

	replaceTorrent(torrent, new_file_path)

	if not client is None :
		client.loadTorrent(torrent)
		for (key, data) in customs_dict.iteritems() :
			client.setCustom(key, torrent, data)

	return tfile.diff(old_torrent, torrent)


###
def update(fetchers_list, client, src_dir_path, backup_dir_path, names_filter, skip_unknown_flag, show_passed_flag, show_diff_flag, save_customs_list) :
	unknown_count = 0
	passed_count = 0
	updated_count = 0
	error_count = 0

	for (torrent_file_name, torrent) in sorted(tfile.torrents(src_dir_path).items(), key=operator.itemgetter(0)) :
		if not names_filter is None and not names_filter in torrent_file_name :
			continue

		unknown_flag = ( not skip_unknown_flag )
		for fetcher in fetchers_list :
			if not fetcher.match(torrent) :
				continue
			unknown_flag = False

			status_line = "[%s] %s %s --- %s" % ("%s", fetcher.plugin(), torrent_file_name, torrent.comment())
			try :
				if not fetcher.loggedIn() :
					fetcher.login()

				if not fetcher.torrentChanged(torrent) :
					tools.cli.oneLine(status_line % (" "), not show_passed_flag)
					passed_count += 1
					continue

				(added_set, removed_set) = updateTorrent(torrent, fetcher, backup_dir_path, client, save_customs_list)
				tools.cli.oneLine(status_line % ("+"), False)
				if show_diff_flag :
					for item in sorted(removed_set) :
						print "\t- %s" % (item)
					for item in sorted(added_set) :
						print "\t+ %s" % (item)
				updated_count += 1

			except fetcherlib.CommonFetcherError, err :
				print (status_line + " :: %s(%s)") % ("-", type(err).__name__, str(err))
				error_count += 1

			except Exception, err :
				print status_line % ("-")
				for row in traceback.format_exc().strip().split("\n") :
					print "\t" + row
				error_count += 1

			break

		if unknown_flag :
			tools.cli.oneLine("[ ] UNKNOWN %s --- %s" % (torrent_file_name, torrent.comment()), False)
			unknown_count += 1

	tools.cli.oneLine("", False)
	print DELIMITER
	print "Unknown: %d" % (unknown_count)
	print "Passed: %d" % (passed_count)
	print "Updated: %d" % (updated_count)
	print "Errors: %d" % (error_count)
	print


##### Main #####
def main() :
	cli_parser = argparse.ArgumentParser(description="Update rtorrent files from popular trackers")
	cli_parser.add_argument("-c", "--config",        dest="config_file_path",   action="store",      required=True, metavar="<file>")
	cli_parser.add_argument("-s", "--source-dir",    dest="src_dir_path",       action="store",      default=".",   metavar="<dir>")
	cli_parser.add_argument("-b", "--backup-dir",    dest="backup_dir_path",    action="store",      default=None,  metavar="<dir>")
	cli_parser.add_argument("-f", "--filter",        dest="names_filter",       action="store",      default=None,  metavar="<substring>")
	cli_parser.add_argument("-o", "--only-fetchers", dest="only_fetchers_list", nargs="+",           default=fetchers.FETCHERS_MAP.keys(), metavar="<plugin>")
	cli_parser.add_argument("-t", "--timeout",       dest="socket_timeout",     action="store",      default=5, type=int, metavar="<seconds>")
	cli_parser.add_argument("-i", "--interative",    dest="interactive_flag",   action="store_true", default=False)
	cli_parser.add_argument("-u", "--skip-unknown",  dest="skip_unknown_flag",  action="store_true", default=False)
	cli_parser.add_argument("-p", "--show-passed",   dest="show_passed_flag",   action="store_true", default=False)
	cli_parser.add_argument("-d", "--show-diff",     dest="show_diff_flag",     action="store_true", default=False)
	cli_parser.add_argument(      "--client",        dest="client_name",        action="store",      default=None, choices=clients.CLIENTS_MAP.keys(), metavar="<plugin>")
	cli_parser.add_argument(      "--client-url",    dest="client_url",         action="store",      default=None, metavar="<url>")
	cli_parser.add_argument(      "--save-customs",  dest="save_customs_list",  nargs="+",           default=None, metavar="<keys>")
	cli_options = cli_parser.parse_args(sys.argv[1:])

	socket.setdefaulttimeout(cli_options.socket_timeout)

	enabled_fetchers_set = set(fetchers.FETCHERS_MAP.keys()).intersection(cli_options.only_fetchers_list)
	fetchers_list = []
	config_parser = ConfigParser.ConfigParser()
	config_parser.read(cli_options.config_file_path)
	for fetcher_name in enabled_fetchers_set :
		fetcher_class = fetchers.FETCHERS_MAP[fetcher_name]
		if config_parser.has_section(fetcher_name) :
			fetchers_list.append(fetcher_class(
					config_parser.get(fetcher_name, "login"),
					config_parser.get(fetcher_name, "passwd"),
					cli_options.interactive_flag,
				))

	if len(enabled_fetchers_set) != len(fetchers.FETCHERS_MAP) :
		cli_options.skip_unknown_flag = True

	if len(fetchers_list) == 0 :
		print >> sys.stderr, "No available fetchers in config"
		sys.exit(1)

	client = None
	if not cli_options.client_name is None :
		client_class = clients.CLIENTS_MAP[cli_options.client_name]
		client = client_class(cli_options.client_url)

	if not client is None and not cli_options.save_customs_list is None :
		cli_options.save_customs_list = list(set(cli_options.save_customs_list))
		valid_keys_list = client.customKeys()
		for key in cli_options.save_customs_list :
			if not key in valid_keys_list :
				print >> sys.stderr, "Invalid custom key: %s" % (key)
				sys.exit(1)


	update(fetchers_list, client,
		cli_options.src_dir_path,
		cli_options.backup_dir_path,
		cli_options.names_filter,
		cli_options.skip_unknown_flag,
		cli_options.show_passed_flag,
		cli_options.show_diff_flag,
		cli_options.save_customs_list,
	)


###
if __name__ == "__main__" :
	main()

