#!/usr/bin/env python2
# -*- coding: utf-8 -*-


import sys
import os
import xmlrpclib


##### Public methods #####
def disableRetrackers(url) :
	server = xmlrpclib.ServerProxy(sys.argv[1])

	multicall = xmlrpclib.MultiCall(server)
	hashes_list = server.download_list()
	for t_hash in hashes_list :
		multicall.t.multicall(t_hash, "", "t.is_enabled=", "t.get_url=")
	trackers_list = list(multicall())

	multicall = xmlrpclib.MultiCall(server)
	for count in xrange(len(hashes_list)) :
		for (index, url) in trackers_list[count] :
			if "retracker.local" in url :
				multicall.t.set_enabled(hashes_list[count], index, 0)
	multicall()


##### Main #####
def main() :
	if len(sys.argv) != 2 :
		print >> sys.stderr, "Usage: %s <http://xmlrpchost/path>" % (os.path.basename(sys.argv[0]))
		print >> sys.stderr, "Warning: rtorrent ONLY!"
		sys.exit(1)
	disableRetrackers(sys.argv[1])


###
if __name__ == "__main__" :
	main()

