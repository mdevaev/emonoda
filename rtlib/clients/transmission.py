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
import transmissionrpc
import xmlrpclib
import time


##### Public constants #####
CLIENT_NAME = "transmission"
DEFAULT_URL = "127.0.0.1"

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
	# XXX: API description: https://trac.transmissionbt.com/browser/trunk/extras/rpc-spec.txt

	def __init__(self, url = DEFAULT_URL) :
		if url is None :
			url = DEFAULT_URL
		clientlib.AbstractClient.__init__(self, url)

		self.__server = transmissionrpc.Client(url)
		#self.__server.set_xmlrpc_size_limit(XMLRPC_SIZE_LIMIT)


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
	@_catchUnknownTorrentFault
	def removeTorrent(self, torrent_hash) :
		#Удаляем торренты, без удаления файлов по их id
		torrentId = self.hashToId(torrent_hash)
		self.__server.remove(torrentId)

	def loadTorrent(self, torrent, prefix = None) :
		torrent_path = torrent.path()
		torrent_hash = torrent.hash()

		assert os.access(torrent_path, os.F_OK), "Torrent file does not exists"
		if not prefix is None :
			assert os.access("%s%s." % (prefix, os.path.sep), os.F_OK), "Invalid prefix"

		
		if prefix != None :
			self.__server.add(torrent_path, 'download_dir' = prefix, 'paused' = False)
		else:
			self.__server.add(torrent_path, 'paused' = False)
			
		"""
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
				time.sleep(LOAD_RETRIES_SLEEP)"""


	@clientlib.hashOrTorrent
	def hasTorrent(self, torrent_hash) :
		#Проверка на существование торрента по хэшу.
		#Возвращает True если существует и False если нет.
		torrentId = self.hashToId(torrent_hash)
		if torrentId != None :
			return True
		else:
			return False

	def hashes(self) :
		#Возвращает список хэшей торрентов
		hashes = []
		for i in self.__server.info().values():
			hashes.append(i.hashString)
		return heshes

	@clientlib.hashOrTorrent
	@_catchUnknownTorrentFault
	def torrentPath(self, torrent_hash) :
		#Возвращает путь к .torrent файлу
		torrentId = self.hashToId(torrent_hash)
		return self.__server.info(torrentId)[torrentId].torrentFile

	@clientlib.hashOrTorrent
	@_catchUnknownTorrentFault
	def dataPrefix(self, torrent_hash) :
		#Возвращает каталог, куда качается торрент
		torrentId = self.hashToId(torrent_hash)
		return self.__server.info(torrentId)[torrentId].downloadDir

	def defaultDataPrefix(self) :
		#Возвращает дефолтный каталог сессии
		return tc.get_session().download_dir

	###

	def customKeys(self) :
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
		multicall = xmlrpclib.MultiCall(self.__server)
		for key in keys_list :
			getattr(multicall.d, "get_custom" + key)(torrent_hash)
		results_list = list(multicall())
		return dict([ (keys_list[index], results_list[index]) for index in xrange(len(keys_list)) ])

	###

	@clientlib.hashOrTorrent
	@_catchUnknownTorrentFault
	def fullPath(self, torrent_hash) :
		#Узнать, если файлов больше, то что возвращать?
		return self.__server.d.get_base_path(torrent_hash)

	@clientlib.hashOrTorrent
	@_catchUnknownTorrentFault
	def name(self, torrent_hash) :
		#Возвращаем имя торрента
		torrentId = self.hashToId(torrent_hash)
		return self.__server.info(torrentId)[torrentId].name

	@clientlib.hashOrTorrent
	@_catchUnknownTorrentFault
	def isSingleFile(self, torrent_hash) :
		#Возвращает True, если в торренте всего один файл, или False, если их много
		torrentId = self.hashToId(torrent_hash)
		count_files = len(self.__server.get_files(torrentId)[torrentId].keys())
		if count_files > 1:
			return False
		else:
			return True
			

	@clientlib.hashOrTorrent
	@_catchUnknownTorrentFault
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
