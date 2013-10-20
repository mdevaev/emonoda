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

from ulib import tools
import ulib.tools.coding # pylint: disable=W0611

import os
import xmlrpclib
import time


##### Public constants #####
CLIENT_NAME = "rtorrent"
DEFAULT_URL = "http://localhost/RPC2"

XMLRPC_SIZE_LIMIT = 67108863
LOAD_RETRIES = 10
LOAD_RETRIES_SLEEP = 1

FAULT_CODE_UNKNOWN_HASH = -501


##### Private methods #####
def _catchUnknownTorrentFault(method) :
	def wrap(self, *args_list, **kwargs_dict) :
		try :
			return method(self, *args_list, **kwargs_dict)
		except xmlrpclib.Fault, err :
			if err.faultCode == FAULT_CODE_UNKNOWN_HASH :
				raise clientlib.NoSuchTorrentError("Unknown torrent hash")
			raise
	return wrap


##### Public classes #####
class Client(clientlib.AbstractClient) :
	# XXX: API description: http://code.google.com/p/gi-torrent/wiki/rTorrent_XMLRPC_reference

	def __init__(self, url = DEFAULT_URL) :
		if url is None :
			url = DEFAULT_URL
		clientlib.AbstractClient.__init__(self, url)

		self.__server = xmlrpclib.ServerProxy(url)
		self.__server.set_xmlrpc_size_limit(XMLRPC_SIZE_LIMIT)


	### Public ###

	@classmethod
	def plugin(cls) :
		return CLIENT_NAME

	###

	@clientlib.hashOrTorrent
	@_catchUnknownTorrentFault
	def removeTorrent(self, torrent_hash) :
		self.__server.d.erase(torrent_hash)

	@clientlib.loadTorrentAccessible
	def loadTorrent(self, torrent, prefix = None) :
		torrent_path = torrent.path()
		torrent_hash = torrent.hash()

		# XXX: https://github.com/rakshasa/rtorrent/issues/22
		# All load_* calls re asynchronous, so we need to wait until the load of torrent files is complete.
		self.__server.load(torrent_path)
		retries = LOAD_RETRIES
		while True :
			try :
				assert self.__server.d.get_hash(torrent_hash).lower() == torrent_hash
				break
			except xmlrpclib.Fault, err :
				if err.faultCode != FAULT_CODE_UNKNOWN_HASH :
					raise
				if retries == 0 :
					raise RuntimeError("Timed torrent uploads after %d seconds" % (LOAD_RETRIES * LOAD_RETRIES_SLEEP))
				retries -= 1
				time.sleep(LOAD_RETRIES_SLEEP)

		if not prefix is None :
			self.__server.d.set_directory(torrent_hash, prefix)
		self.__server.d.start(torrent_hash)

	@clientlib.hashOrTorrent
	def hasTorrent(self, torrent_hash) :
		try :
			assert self.__server.d.get_hash(torrent_hash).lower() == torrent_hash
			return True
		except xmlrpclib.Fault, err :
			if err.faultCode != FAULT_CODE_UNKNOWN_HASH :
				raise
		return False

	def hashes(self) :
		return map(str.lower, self.__server.download_list())

	@clientlib.hashOrTorrent
	@_catchUnknownTorrentFault
	def torrentPath(self, torrent_hash) :
		return self.__server.d.get_loaded_file(torrent_hash)

	@clientlib.hashOrTorrent
	@_catchUnknownTorrentFault
	def dataPrefix(self, torrent_hash) :
		multicall = xmlrpclib.MultiCall(self.__server)
		multicall.d.get_directory(torrent_hash)
		multicall.d.is_multi_file(torrent_hash)
		(path, is_multi_file) = multicall()
		if is_multi_file :
			path = os.path.dirname(os.path.normpath(path))
		return path

	def defaultDataPrefix(self) :
		return self.__server.get_directory()

	###

	@classmethod
	def customKeys(cls) :
		return ("1", "2", "3", "4", "5")

	@clientlib.hashOrTorrent
	@_catchUnknownTorrentFault
	def setCustoms(self, torrent_hash, customs_dict) :
		assert len(customs_dict) != 0, "Empty customs list"
		multicall = xmlrpclib.MultiCall(self.__server)
		for (key, value) in customs_dict.iteritems() :
			getattr(multicall.d, "set_custom" + key)(torrent_hash, value)
		multicall()

	@clientlib.hashOrTorrent
	@_catchUnknownTorrentFault
	def customs(self, torrent_hash, keys_list) :
		assert len(keys_list) != 0, "Empty customs list"
		keys_list = list(set(keys_list))
		multicall = xmlrpclib.MultiCall(self.__server)
		for key in keys_list :
			getattr(multicall.d, "get_custom" + key)(torrent_hash)
		results_list = list(multicall())
		return dict([ (keys_list[index], results_list[index]) for index in xrange(len(keys_list)) ])

	###

	@clientlib.hashOrTorrent
	@_catchUnknownTorrentFault
	def fullPath(self, torrent_hash) :
		return self.__server.d.get_base_path(torrent_hash)

	@clientlib.hashOrTorrent
	@_catchUnknownTorrentFault
	def name(self, torrent_hash) :
		return self.__server.d.get_name(torrent_hash)

	@clientlib.hashOrTorrent
	@_catchUnknownTorrentFault
	def isSingleFile(self, torrent_hash) :
		return not self.__server.d.is_multi_file(torrent_hash)

	@clientlib.hashOrTorrent
	@_catchUnknownTorrentFault
	def files(self, torrent_hash, system_path_flag = False) :
		multicall = xmlrpclib.MultiCall(self.__server)
		multicall.d.get_base_path(torrent_hash)
		multicall.d.get_base_filename(torrent_hash)
		multicall.d.is_multi_file(torrent_hash)
		multicall.d.get_size_files(torrent_hash)
		multicall.f.get_size_bytes(torrent_hash, 0)
		(base_path, base_file_name, is_multi_file, count, first_file_size) = tuple(multicall())
		base = tools.coding.utf8( base_path if system_path_flag else base_file_name )

		if not is_multi_file :
			return { base : { "size" : first_file_size, "md5" : None } }

		multicall = xmlrpclib.MultiCall(self.__server)
		for index in xrange(count) :
			multicall.f.get_path(torrent_hash, index)
			multicall.f.get_size_bytes(torrent_hash, index)
		files_list = list(multicall())
		files_list = zip(files_list[::2], files_list[1::2])

		files_dict = { base : None }
		for (path, size) in files_list :
			path_list = tools.coding.utf8(path).split(os.path.sep)
			name = None
			for index in xrange(len(path_list)) :
				name = os.path.join(base, os.path.sep.join(path_list[0:index+1]))
				files_dict[name] = None
			assert not name is None
			files_dict[name] = { "size" : size, "md5" : None }
		return files_dict

