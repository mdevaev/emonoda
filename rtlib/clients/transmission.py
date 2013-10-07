# -*- coding: UTF-8 -*-
#
#    rtfetch -- Update rtorrent files from popular trackers
#    Copyright (C) 2013  Vitaly Lipatov <lav@etersoft.ru>
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
import time

import transmissionrpc

##### Public constants #####
CLIENT_NAME = "transmission"
DEFAULT_URL = "http://sample.com:9091/transmission/rpc"
LOGIN = "user"
PASSWORD = "password"

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
	# XXX: API description: http://pythonhosted.org/transmissionrpc/

	def __init__(self, url = DEFAULT_URL) :
		if url is None :
			url = DEFAULT_URL
		clientlib.AbstractClient.__init__(self, url)

		self.__server = transmissionrpc.Client(DEFAULT_URL, port = 9091, user = LOGIN, password = PASSWORD)

	### Public ###

	@classmethod
	def plugin(cls) :
		return CLIENT_NAME

	###

	@clientlib.hashOrTorrent
	@_catchUnknownTorrentFault
	def removeTorrent(self, torrent_hash) :
		self.__server.remove_torrent(torrent_hash)

	def loadTorrent(self, torrent, prefix = None) :
		torrent_path = torrent.path()
		torrent_hash = torrent.hash()

		assert os.access(torrent_path, os.F_OK), "Torrent file does not exists"
		if not prefix is None :
			assert os.access("%s%s." % (prefix, os.path.sep), os.F_OK), "Invalid prefix"

		__server.add_torrent(torrent_path)

	@clientlib.hashOrTorrent
	def hasTorrent(self, torrent_hash) :
		assert __server.get_torrent(torrent_hash, arguments='hashString').hashString == torrent_hash
		return True

	#def hashes(self) :
	#	#return map(str.lower, self.__server.download_list())
	#	assert None, "TODO: hashes"

	#@clientlib.hashOrTorrent
	#@_catchUnknownTorrentFault
	#def torrentPath(self, torrent_hash) :
	#	#return self.__server.d.get_loaded_file(torrent_hash)
	#	assert None, "TODO: torrentPath"

	#@clientlib.hashOrTorrent
	#@_catchUnknownTorrentFault
	#def dataPrefix(self, torrent_hash) :
	#	multicall = xmlrpclib.MultiCall(self.__server)
	#	multicall.d.get_directory(torrent_hash)
	#	multicall.d.is_multi_file(torrent_hash)
	#	(path, is_multi_file) = multicall()
	#	if is_multi_file :
	#		path = os.path.dirname(os.path.normpath(path))
	#	return path

	#def defaultDataPrefix(self) :
	#	return self.__server.get_directory()

	###
#[01:33:16] <Devaev Maxim> еще важно, про files()
#[01:33:24] <Devaev Maxim> он должен включать в себе еще и каталоги
#[01:33:36] <Devaev Maxim> у которых словарик с атрибутами равен None

	@clientlib.hashOrTorrent
	@_catchUnknownTorrentFault
	def files(self, torrent_hash, system_path_flag = False) :
		torrent_files = rreturn __server.get_files(torrent_hash)
		#base = tools.coding.utf8
		files_dict = { base : None }
		for (numtor, allfiles) in torrent_files.iteritems():
		for (numfile, value) in allfiles.iteritems():
			files_dict[value['name']] = { "size" : value['size'], "md5" : None }
			# TODO: Каталоги (none)
		return files_dict

