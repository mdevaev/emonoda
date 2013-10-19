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
from rtlib import clientlib
from rtlib import clients
from rtlib import config

from ulib import tools
import ulib.tools.cli # pylint: disable=W0611
import ulib.tools.fmt

import sys
import os
import socket
import operator
import shutil
import time


##### Public constants #####
DELIMITER = "-" * 10


##### Public methods #####
def updateTorrent(torrent, fetcher, backup_dir_path, client, save_customs_list, real_update_flag) :
	new_data = fetcher.fetchTorrent(torrent)
	tmp_torrent = tfile.Torrent()
	tmp_torrent.loadData(new_data)
	diff_tuple = tfile.diff(torrent, tmp_torrent)

	if real_update_flag :
		if not backup_dir_path is None :
			backup_file_path = os.path.join(backup_dir_path, "%s.%d.bak" % (os.path.basename(torrent.path()), time.time()))
			shutil.copyfile(torrent.path(), backup_file_path)

		if not client is None :
			if len(save_customs_list) != 0 :
				customs_dict = client.customs(torrent, save_customs_list)
			prefix = client.dataPrefix(torrent)
			client.removeTorrent(torrent)

		with open(torrent.path(), "w") as torrent_file :
			torrent_file.write(new_data)
		torrent.loadData(new_data, torrent.path())

		if not client is None :
			client.loadTorrent(torrent, prefix)
			if len(save_customs_list) != 0 :
				client.setCustoms(torrent, customs_dict)

	return diff_tuple

def torrents(src_dir_path, names_filter) :
	torrents_list = tfile.torrents(src_dir_path).items()
	if not names_filter is None :
		torrents_list = [ item for item in torrents_list if names_filter in item[0] ]
	return sorted(torrents_list, key=operator.itemgetter(0))


###
def update(fetchers_list, client,
		src_dir_path,
		backup_dir_path,
		names_filter,
		save_customs_list,
		skip_unknown_flag,
		pass_failed_login_flag,
		show_passed_flag,
		show_diff_flag,
		real_update_flag,
		no_colors_flag,
		force_colors_flag,
	) :

	invalid_count = 0
	not_in_client_count = 0
	unknown_count = 0
	passed_count = 0
	updated_count = 0
	error_count = 0

	torrents_list = torrents(src_dir_path, names_filter)
	hashes_list = ( client.hashes() if not client is None else [] )

	if not no_colors_flag :
		colored = ( lambda codes_list, text : ulib.tools.term.colored(codes_list, text, force_colors_flag) )
	else :
		colored = ( lambda codes_list, text : text )
	make_fail = ( lambda text : (colored(31, "!"), colored(31, text)) )

	for (count, (torrent_file_name, torrent)) in enumerate(torrents_list) :
		status_line = "[%%s] %s %%s %s" % (tools.fmt.formatProgress(count + 1, len(torrents_list)), torrent_file_name)

		if torrent is None :
			tools.cli.newLine(status_line % (make_fail("INVALID_TORRENT")))
			invalid_count += 1
			continue

		status_line += " --- %s" % (torrent.comment() or "")

		if not client is None and not torrent.hash() in hashes_list :
			tools.cli.newLine(status_line % (make_fail("NOT_IN_CLIENT")))
			not_in_client_count += 1
			continue

		fetcher = fetcherlib.selectFetcher(torrent, fetchers_list)
		if fetcher is None :
			unknown_count += 1
			if not skip_unknown_flag :
				tools.cli.newLine(status_line % (make_fail("UNKNOWN")))
			continue

		status_line = status_line % ("%s", fetcher.plugin())
		try :
			if not fetcher.loggedIn() :
				tools.cli.newLine(status_line % (colored(33, "?")))
				error_count += 1
				continue

			if not fetcher.torrentChanged(torrent) :
				tools.cli.oneLine(status_line % (" "), not show_passed_flag)
				passed_count += 1
				continue

			diff_tuple = updateTorrent(torrent, fetcher, backup_dir_path, client, save_customs_list, real_update_flag)
			tools.cli.newLine(status_line % (colored(32, "+")))
			if show_diff_flag :
				tfile.printDiff(diff_tuple, "\t", use_colors_flag=(not no_colors_flag), force_colors_flag=force_colors_flag)
			updated_count += 1

		except fetcherlib.CommonFetcherError, err :
			tools.cli.newLine((status_line + " :: %s(%s)") % (colored(31, "-"), type(err).__name__, str(err)))
			error_count += 1

		except Exception, err :
			tools.cli.newLine(status_line % ("-"))
			tools.cli.printTraceback("\t")
			error_count += 1

	if ( (client and not_in_client_count) or (not skip_unknown_flag and unknown_count) or (show_passed_flag and passed_count) or
		invalid_count or updated_count or error_count ) :
		tools.cli.newLine("")
	tools.cli.newLine(DELIMITER)

	print "Invalid:       %d" % (invalid_count)
	if not client is None :
		print "Not in client: %d" % (not_in_client_count)
	print "Unknown:       %d" % (unknown_count)
	print "Passed:        %d" % (passed_count)
	print "Updated:       %d" % (updated_count)
	print "Errors:        %d" % (error_count)
	print


###
def initFetchers(config_dict, url_retries, url_sleep_time, proxy_url, interactive_flag, only_fetchers_list, pass_failed_login_flag) :
	fetchers_list = []
	for fetcher_name in set(fetchers.FETCHERS_MAP.keys()).intersection(only_fetchers_list) :
		get_fetcher_option = ( lambda option : config.getOption(fetcher_name, option, config_dict) )
		get_common_option = ( lambda option, cli_value : config.getCommonOption((
			config.SECTION_MAIN, config.SECTION_RTFETCH, fetcher_name), option, config_dict, cli_value) )

		fetcher_class = fetchers.FETCHERS_MAP[fetcher_name]
		if config_dict.has_key(fetcher_name) :
			tools.cli.oneLine("# Enabling the fetcher \"%s\"..." % (fetcher_name))

			f_login            = get_fetcher_option(config.OPTION_LOGIN)
			f_passwd           = get_fetcher_option(config.OPTION_PASSWD)
			f_url_retries      = get_common_option(config.OPTION_URL_RETRIES, url_retries)
			f_url_sleep_time   = get_common_option(config.OPTION_URL_SLEEP_TIME, url_sleep_time)
			f_proxy_url        = get_common_option(config.OPTION_PROXY_URL, proxy_url)
			f_interactive_flag = get_common_option(config.OPTION_INTERACTIVE, interactive_flag)

			try :
				fetcher = fetcher_class(f_login, f_passwd, f_url_retries, f_url_sleep_time, f_proxy_url, f_interactive_flag)
				fetcher.login()
				tools.cli.newLine("# Fetcher \"%s\" is ready (user: %s; proxy: %s; interactive: %s)" % (
						fetcher_name,
						( f_login or "<anonymous>" ),
						( f_proxy_url or "<none>" ),
						( "yes" if f_interactive_flag else "no" ),
					))
			except Exception, err :
				tools.cli.newLine("# Init error: %s: %s(%s)" % (fetcher_name, type(err).__name__, err))
				if not pass_failed_login_flag :
					raise
			fetchers_list.append(fetcher)
	return fetchers_list


##### Main #####
def main() :
	(cli_parser, config_dict, argv_list) = config.partialParser(sys.argv[1:], description="Update rtorrent files from popular trackers")
	config.addArguments(cli_parser,
		config.ARG_SOURCE_DIR,
		config.ARG_BACKUP_DIR,
		config.ARG_NAMES_FILTER,
		config.ARG_ONLY_FETCHERS,
		config.ARG_TIMEOUT,
		config.ARG_INTERACTIVE,
		config.ARG_NO_INTERACTIVE,
		config.ARG_SKIP_UNKNOWN,
		config.ARG_NO_SKIP_UNKNOWN,
		config.ARG_PASS_FAILED_LOGIN,
		config.ARG_NO_PASS_FAILED_LOGIN,
		config.ARG_SHOW_PASSED,
		config.ARG_NO_SHOW_PASSED,
		config.ARG_SHOW_DIFF,
		config.ARG_NO_SHOW_DIFF,
		config.ARG_CHECK_VERSIONS,
		config.ARG_NO_CHECK_VERSIONS,
		config.ARG_REAL_UPDATE,
		config.ARG_NO_REAL_UPDATE,
		config.ARG_URL_RETRIES,
		config.ARG_URL_SLEEP_TIME,
		config.ARG_PROXY_URL,
		config.ARG_CLIENT,
		config.ARG_CLIENT_URL,
		config.ARG_SAVE_CUSTOMS,
		config.ARG_NO_COLORS,
		config.ARG_USE_COLORS,
		config.ARG_FORCE_COLORS,
		config.ARG_NO_FORCE_COLORS,
	)
	cli_options = cli_parser.parse_args(argv_list)
	config.syncParsers(config.SECTION_RTFETCH, cli_options, config_dict, (
			# For fetchers: validate this options later
			config.OPTION_LOGIN,
			config.OPTION_PASSWD,
			config.OPTION_URL_RETRIES,
			config.OPTION_URL_SLEEP_TIME,
			config.OPTION_PROXY_URL,
			config.OPTION_INTERACTIVE,
		))


	socket.setdefaulttimeout(cli_options.socket_timeout)

	fetchers_list = initFetchers(config_dict,
		cli_options.url_retries,
		cli_options.url_sleep_time,
		cli_options.proxy_url,
		cli_options.interactive_flag,
		cli_options.only_fetchers_list,
		cli_options.pass_failed_login_flag,
	)
	if len(fetchers_list) == 0 :
		print >> sys.stderr, "No available fetchers in config"
		sys.exit(1)
	if len(fetchers_list) != len(fetchers.FETCHERS_MAP) :
		cli_options.skip_unknown_flag = True

	if cli_options.check_versions_flag and not fetcherlib.checkVersions(fetchers_list) :
		sys.exit(1)

	print

	client = None
	if not cli_options.client_name is None :
		client = clientlib.initClient(
			clients.CLIENTS_MAP[cli_options.client_name],
			cli_options.client_url,
			save_customs_list=cli_options.save_customs_list,
		)

	update(fetchers_list, client,
		cli_options.src_dir_path,
		cli_options.backup_dir_path,
		cli_options.names_filter,
		cli_options.save_customs_list,
		cli_options.skip_unknown_flag,
		cli_options.pass_failed_login_flag,
		cli_options.show_passed_flag,
		cli_options.show_diff_flag,
		cli_options.real_update_flag,
		cli_options.no_colors_flag,
		cli_options.force_colors_flag,
	)


###
if __name__ == "__main__" :
	main()

