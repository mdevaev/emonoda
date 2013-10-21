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
		raise RuntimeError("NOT TESTED! Comment this line and try again on your own risk! Backup your data!") # FIXME FIXME FIXME!!!
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
	
	def hashToId(torrent_hash):
		torrents = self.__server.info()
		torrentId = None
		for i,j in torrents.items():
			if j.hash.String == __hash :
					torrentId = i
					break
		return torrentId				
		
		

	@clientlib.hashOrTorrent
	def removeTorrent(self, torrent_hash) :
		# TODO: raise clientlib.NoSuchTorrentError for non-existent torrent
		self.__server.remove_torrent(torrent_hash)

	@clientlib.loadTorrentAccessible
	def loadTorrent(self, torrent, prefix = None) :
		torrent_path = torrent.path()
		kwargs_dict = { "paused" : False }
		if not prefix is None :
			kwargs_dict["download_dir"] = prefix
		self.__server.add_torrent(torrent_path, **kwargs_dict)

	@clientlib.hashOrTorrent
	def hasTorrent(self, torrent_hash) :
		torrent_obj = self.__server.get_torrent(torrent_hash, arguments=("hashString",))
		if not torrent_obj is None :
			assert torrent_obj.hashString.lower() == torrent_hash
			return True
		return False

	def hashes(self) :
		return [ item.hashString.lower() for item in self.__server.get_torrents(arguments=("id", "hashString")) ]

	@clientlib.hashOrTorrent
	def torrentPath(self, torrent_hash) :
		# TODO: raise clientlib.NoSuchTorrentError for non-existent torrent
		#Возвращает путь к .torrent файлу
		torrentId = self.hashToId(torrent_hash)
		return self.__server.info(torrentId)[torrentId].torrentFile

	@clientlib.hashOrTorrent
	def dataPrefix(self, torrent_hash) :
		torrent_obj = self.__server.get_torrent(torrent_hash, arguments=("id", "hashString", "downloadDir",))
		if torrent_obj is None :
			raise clientlib.NoSuchTorrentError("Unknown torrent hash")
		assert torrent_obj.hashString.lower() == torrent_hash
		return torrent_obj.downloadDir

	def defaultDataPrefix(self) :
		session = self.__server.get_session()
		return session.download_dir

	###

	@clientlib.hashOrTorrent
	def fullPath(self, torrent_hash) :
		# TODO: raise clientlib.NoSuchTorrentError for non-existent torrent
		#return self.__server.d.get_base_path(torrent_hash)
		raise NotImplementedError # TODO

	@clientlib.hashOrTorrent
	def name(self, torrent_hash) :
		#Возвращаем имя торрента
		torrentId = self.hashToId(torrent_hash)
		return self.__server.info(torrentId)[torrentId].name

	@clientlib.hashOrTorrent
	def isSingleFile(self, torrent_hash) :
		#Возвращает True, если в торренте всего один файл, или False, если их много
		torrentId = self.hashToId(torrent_hash)
		count_files = len(self.__server.get_files(torrentId)[torrentId].keys())
		if count_files > 1:
			return False
		else:
			return True
			

	@clientlib.hashOrTorrent
	def files(self, torrent_hash, system_path_flag = False) :
		#тут все сложно, нужно вернуть сложный словарь списка файлов.
		#если установлен system_path_flag, то путь должен быть полным, иначе пути относительно каталога, куда скачиваем торрент
		torrentId = self.hashToId(torrent_hash)
		files_dict = {}
		dirs_dict = []
		prefix = ""
		if system_path_flag :
			prefix = os.path.sep.join([self.__server.info(torrentId)[torrentId].downloadDir, ""])
		if self.isSingleFile(torrent_hash):
			i = self.__server.get_files(torrentId)[torrentId][0]
			return { "".join(prefix,i['name']) : { 'size' : i['size'] }}
		for i in self.__server.get_files(torrentId)[torrentId].values():
			dirname = os.path.dirname(i['name']
			if dirname not in dir_dict:
				dir_dict.append(dirname)
				files_dict["".join([prefix,dirname])] = None
			files_dict["".join([prefix,i['name']])] = { 'size' : i['size'] }
		return files_dict

