# -*- coding: UTF-8 -*-
#
#    transmission client for rtfetch
#    Copyright (C) 2013  Vitaly Lipatov <lav@etersoft.ru>, Devaev Maxim <mdevaev@gmail.com>
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

import os
import operator

try :
	import transmissionrpc # pylint: disable=F0401
except ImportError :
	transmissionrpc = None # pylint: disable=C0103


##### Public constants #####
CLIENT_NAME = "transmission"
DEFAULT_URL = "http://localhost:9091/transmission/rpc"

LOAD_RETRIES = 10
LOAD_RETRIES_SLEEP = 1

FAULT_CODE_UNKNOWN_HASH = -501


##### Public classes #####
class Client(clientlib.AbstractClient) :
	# XXX: API description: http://pythonhosted.org/transmissionrpc/

	def __init__(self, url = DEFAULT_URL) :
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

	@clientlib.loadTorrentAccessible
	def loadTorrent(self, torrent, prefix = None) :
		torrent_path = torrent.path()
		kwargs_dict = { "paused" : False }
		if not prefix is None :
			kwargs_dict["download_dir"] = prefix
		self.__server.add_torrent(torrent_path, **kwargs_dict)

	@clientlib.hashOrTorrent
	def hasTorrent(self, torrent_hash) :
		try :
			self.__getTorrent(torrent_hash)
			return True
		except clientlib.NoSuchTorrentError :
			return False

	def hashes(self) :
		return [ item.hashString.lower() for item in self.__server.get_torrents(arguments=("id", "hashString")) ]

	@clientlib.hashOrTorrent
	def torrentPath(self, torrent_hash) :
		return self.__getTorrent(torrent_hash).torrentFile

	@clientlib.hashOrTorrent
	def dataPrefix(self, torrent_hash) :
		return self.__getTorrent(torrent_hash, args_list=("downloadDir",)).downloadDir

	def defaultDataPrefix(self) :
		session = self.__server.get_session()
		assert not session is None
		return session.download_dir

	###

	@clientlib.hashOrTorrent
	def fullPath(self, torrent_hash) :
		# TODO: raise clientlib.NoSuchTorrentError for non-existent torrent
		#return self.__server.d.get_base_path(torrent_hash)
		raise NotImplementedError # TODO

	@clientlib.hashOrTorrent
	def name(self, torrent_hash) :
		return self.__getTorrent(torrent_hash, args_list=("name",)).name

	@clientlib.hashOrTorrent
	def isSingleFile(self, torrent_hash) :
		files_dict = self.__getFiles(torrent_hash)
		if len(files_dict) > 1 :
			return True
		return ( not os.path.sep in files_dict.values()[0]["name"] )

	@clientlib.hashOrTorrent
	def files(self, torrent_hash, system_path_flag = False) :
		#тут все сложно, нужно вернуть сложный словарь списка файлов.
		#если установлен system_path_flag, то путь должен быть полным, иначе пути относительно каталога, куда скачиваем торрент
		t_files_dict = self.__getFiles(torrent_hash)
		files_dict = {}
		dirs_dict = []
		prefix = ( self.dataPrefix(torrent_hash) if system_path_flag else "" )
		if self.isSingleFile(torrent_hash):
			i = t_files_dict[0]
			return { "".join(prefix,i['name']) : { 'size' : i['size'] }}
		for i in t_files_dict.values():
			dirname = os.path.dirname(i['name'])
			if dirname not in dirs_dict:
				dirs_dict.append(dirname)
				files_dict["".join([prefix,dirname])] = None
			files_dict["".join([prefix,i['name']])] = { 'size' : i['size'] }
		return files_dict

	### Private ###

	def __getTorrent(self, torrent_hash, args_list = ()) :
		args_set = set(args_list).union(("id", "hashString"))
		torrent_obj = self.__server.get_torrent(torrent_hash, arguments=tuple(args_set))
		if torrent_obj is None: # FIXME: Is that right?
			raise clientlib.NoSuchTorrentError("Unknown torrent hash")
		assert torrent_obj.hashString.lower() == torrent_hash
		return torrent_obj

	def __getFiles(self, torrent_hash) :
		files_dict = self.__server.get_file(torrent_hash)
		if len(files_dict) == 0 : # FIXME: Is that right?
			raise clientlib.NoSuchTorrentError("Unknown torrent hash")
		assert len(files_dict) == 1
		files_dict = files_dict.values()[0]
		assert len(files_dict) > 0
		return files_dict

