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

from ulib import tools
import ulib.tools.coding # pylint: disable=W0611

import os
import time

try :
    import transmissionrpc
except ImportError :
    transmissionrpc = None

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

	def hashes(self) :
		# TODO: check what with arguments here
		#return map(lambda x:x.hashString, self.__server.get_torrents(arguments='hashString'))
		return map(lambda x:x.hashString, self.__server.get_torrents())

	@clientlib.hashOrTorrent
	@_catchUnknownTorrentFault
	def files(self, torrent_hash, system_path_flag = False) :
		torrent_files = __server.get_files(torrent_hash)
		#base = tools.coding.utf8
		files_dict = { base : None }
		for (numtor, allfiles) in torrent_files.iteritems():
			for (numfile, value) in allfiles.iteritems():
				files_dict[value['name']] = { "size" : value['size'], "md5" : None }
				# TODO: Нужно включать каталоги с атрибутом (none)
		return files_dict

