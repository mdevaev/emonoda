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


from rtlib import clientlib

from rtlib import tools
import rtlib.tools.coding # pylint: disable=W0611

import os
import xmlrpclib


##### Public constants #####
CLIENT_NAME = "rtorrent"
DEFAULT_URL = "http://localhost/RPC2"

XMLRPC_SIZE_LIMIT = 67108863


##### Public classes #####
class Client(clientlib.AbstractClient) :
	# XXX: API description: http://code.google.com/p/gi-torrent/wiki/rTorrent_XMLRPC_reference

	def __init__(self, url = DEFAULT_URL) :
		if url is None :
			url = DEFAULT_URL
		clientlib.AbstractClient.__init__(self, url = DEFAULT_URL)

		self.__server = xmlrpclib.ServerProxy(url)
		self.__server.set_xmlrpc_size_limit(XMLRPC_SIZE_LIMIT)


	### Public ###

	@classmethod
	def plugin(cls) :
		return CLIENT_NAME

	@clientlib.hashOrTorrent
	def removeTorrent(self, torrent_hash) :
		self.__server.d.erase(torrent_hash)

	def loadTorrent(self, torrent) :
		self.__server.load_start(torrent.path())

	def hashs(self) :
		return self.__server.download_list()

	@clientlib.hashOrTorrent
	def torrentPath(self, torrent_hash) :
		return self.__server.d.get_loaded_file(torrent_hash)

	###

	def customKeys(self) :
		return ("1", "2", "3", "4", "5")

	@clientlib.hashOrTorrent
	def setCustom(self, torrent_hash, key, data) :
		method = getattr(self.__server.d, "set_custom" + key)
		method(torrent_hash, data)

	@clientlib.hashOrTorrent
	def custom(self, torrent_hash, key) :
		method = getattr(self.__server.d, "get_custom" + key)
		return method(torrent_hash)

	###

	@clientlib.hashOrTorrent
	def fullPath(self, torrent_hash) :
		return self.__server.d.get_base_path(torrent_hash)

	@clientlib.hashOrTorrent
	def name(self, torrent_hash) :
		return self.__server.d.get_name(torrent_hash)

	@clientlib.hashOrTorrent
	def isSingleFile(self, torrent_hash) :
		return not self.__server.d.is_multi_file(torrent_hash)

	@clientlib.hashOrTorrent
	def files(self, torrent_hash, system_path_flag = False) :
		method = ( self.__server.d.get_base_path if system_path_flag else self.__server.d.get_base_filename )
		base = tools.coding.utf8(method(torrent_hash))
		files_set = set([base])
		if self.isSingleFile(torrent_hash) :
			return files_set

		count = self.__server.d.get_size_files(torrent_hash)
		multicall = xmlrpclib.MultiCall(self.__server)
		for index in xrange(count) :
			multicall.f.get_path(torrent_hash, index)

		fetched_list = list(multicall())
		for count in xrange(len(fetched_list)) :
			path = tools.coding.utf8(fetched_list[count])
			path_list = path.split(os.path.sep)
			for index in xrange(len(path_list)) :
				files_set.add(os.path.join(base, os.path.sep.join(path_list[0:index+1])))
		return files_set

