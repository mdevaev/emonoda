#!/usr/bin/env python2
# -*- coding: utf-8 -*-


try :
	from rtlib.config import DEFAULT_TIMEOUT
	from rtlib.clients.rtorrent import DEFAULT_URL
except ImportError :
	DEFAULT_TIMEOUT = 5
	DEFAULT_URL = "http://localhost/RPC2"

import sys
import socket
import xmlrpclib
import argparse


##### Public methods #####
def manageTrackers(client_url, enable_list, disable_list) :
	server = xmlrpclib.ServerProxy(client_url)

	multicall = xmlrpclib.MultiCall(server)
	hashes_list = server.download_list()
	for t_hash in hashes_list :
		multicall.t.multicall(t_hash, "", "t.is_enabled=", "t.get_url=")
	trackers_list = list(multicall())

	actions_dict = dict.fromkeys(set(enable_list or ()), 1)
	actions_dict.update(dict.fromkeys(set(disable_list or ()), 0))

	multicall = xmlrpclib.MultiCall(server)
	for count in xrange(len(hashes_list)) :
		for (index, (is_enabled, url)) in enumerate(trackers_list[count]) :
			for (pattern, action) in actions_dict.iteritems() :
				if pattern in url and action != is_enabled :
					multicall.t.set_enabled(hashes_list[count], index, action)
					print url, pattern, action
					continue
	multicall()


##### Main #####
def main() :
	cli_parser = argparse.ArgumentParser(description="Manage trackers (rtorrent only)")
	cli_parser.add_argument(      "--enable",     dest="enable_list",  nargs="+", metavar="<pattern>")
	cli_parser.add_argument(      "--disable",    dest="disable_list", nargs="+", metavar="<pattern>")
	cli_parser.add_argument("-t", "--timeout",    dest="socket_timeout", action="store", default=DEFAULT_TIMEOUT, type=int, metavar="<seconds>")
	cli_parser.add_argument(      "--client-url", dest="client_url",     action="store", default=DEFAULT_URL, metavar="<url>")

	cli_options = cli_parser.parse_args(sys.argv[1:])
	socket.setdefaulttimeout(cli_options.socket_timeout)
	manageTrackers(
		cli_options.client_url,
		cli_options.enable_list,
		cli_options.disable_list,
	)


###
if __name__ == "__main__" :
	main()

