# -*- coding: UTF-8 -*-
#
#    transmission client for rtfetch
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

#from ulib import tools
#import ulib.tools.coding # pylint: disable=W0611

import os
import operator

try :
	import transmissionrpc # pylint: disable=F0401
except ImportError :
	transmissionrpc = None # pylint: disable=C0103


##### Public constants #####
CLIENT_NAME = "transmission"
DEFAULT_URL = "http://localhost:9091/transmission/rpc/"

LOAD_RETRIES = 10
LOAD_RETRIES_SLEEP = 1

FAULT_CODE_UNKNOWN_HASH = -501


##### Public classes #####
class Client(clientlib.AbstractClient) :
	# XXX: API description: http://pythonhosted.org/transmissionrpc/

	def __init__(self, url = DEFAULT_URL) :
		raise RuntimeError("NOT IMPLEMENTED!") # FIXME FIXME FIXME!!!
		if transmissionrpc is None :
			raise RuntimeError("Required module transmissionrpc")

		if url is None :
			url = DEFAULT_URL
		clientlib.AbstractClient.__init__(self, url)

		# Client uses urlparse for get user and password from URL
		self.__server = transmissionrpc.Client(url)


	### Public ###

	@classmethod
	def plugin(cls) :
		return CLIENT_NAME

	###

	@clientlib.hashOrTorrent
	def removeTorrent(self, torrent_hash) :
		# TODO: raise clientlib.NoSuchTorrentError for non-existent torrent
		self.__server.remove_torrent(torrent_hash)

	def loadTorrent(self, torrent, prefix = None) :
		torrent_path = torrent.path()
		assert os.access(torrent_path, os.F_OK), "Torrent file does not exists"
		if not prefix is None :
			assert os.access("%s%s." % (prefix, os.path.sep), os.F_OK), "Invalid prefix"
		self.__server.add_torrent(torrent_path)

	@clientlib.hashOrTorrent
	def hasTorrent(self, torrent_hash) :
		torrent_obj = self.__server.get_torrent(torrent_hash, arguments=("hashString",))
		if not torrent_obj is None :
			assert torrent_obj.hashString.lower() == torrent_hash
			return True
		return False

	def hashes(self) :
		return [ item.hashString.lower() for item in self.__server.get_torrents(arguments=("hashString",)) ]

	@clientlib.hashOrTorrent
	def torrentPath(self, torrent_hash) :
		# TODO: raise clientlib.NoSuchTorrentError for non-existent torrent
		#return self.__server.d.get_loaded_file(torrent_hash)
		raise NotImplementedError # TODO

	@clientlib.hashOrTorrent
	def dataPrefix(self, torrent_hash) :
		# TODO: raise clientlib.NoSuchTorrentError for non-existent torrent
		#multicall = xmlrpclib.MultiCall(self.__server)
		#multicall.d.get_directory(torrent_hash)
		#multicall.d.is_multi_file(torrent_hash)
		#(path, is_multi_file) = multicall()
		#if is_multi_file :
		#	path = os.path.dirname(os.path.normpath(path))
		#return path
		raise NotImplementedError # TODO

	def defaultDataPrefix(self) :
		#return self.__server.get_directory()
		raise NotImplementedError # TODO

	###

	@clientlib.hashOrTorrent
	def fullPath(self, torrent_hash) :
		# TODO: raise clientlib.NoSuchTorrentError for non-existent torrent
		#return self.__server.d.get_base_path(torrent_hash)
		raise NotImplementedError # TODO

	@clientlib.hashOrTorrent
	def name(self, torrent_hash) :
		# TODO: raise clientlib.NoSuchTorrentError for non-existent torrent
		#return self.__server.d.get_name(torrent_hash)
		raise NotImplementedError # TODO

	@clientlib.hashOrTorrent
	def isSingleFile(self, torrent_hash) :
		# TODO: raise clientlib.NoSuchTorrentError for non-existent torrent
		#return not self.__server.d.is_multi_file(torrent_hash)
		raise NotImplementedError # TODO

	@clientlib.hashOrTorrent
	def files(self, torrent_hash, system_path_flag = False) :
		# TODO: raise clientlib.NoSuchTorrentError for non-existent torrent
		torrent_files = self.__server.get_files(torrent_hash)
		#base = tools.coding.utf8
		base = None # FIXME!
		files_dict = { base : None }
		#for (numtor, allfiles) in torrent_files.iteritems():
		for allfiles in torrent_files.values() :
			#for (numfile, value) in allfiles.iteritems():
			for value in allfiles.values() :
				files_dict[value['name']] = { "size" : value['size'], "md5" : None }
				# TODO: Нужно включать каталоги с атрибутом (none)
		return files_dict

