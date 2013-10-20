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


import os

import tfile

import ulib.validators.common


##### Exceptions #####
class NoSuchTorrentError(Exception) :
	pass


##### Public methods #####
def initClient(client_class, client_url, save_customs_list = (), set_customs_dict = None) :
	set_customs_dict = ( set_customs_dict or {} )
	valid_customs_list = client_class.customKeys()
	for custom_key in list(save_customs_list) + list(set_customs_dict) :
		ulib.validators.common.validRange(custom_key, valid_customs_list)
	return client_class(client_url)


###
def indexed(client, system_path_flag = False) :
	files_dict = {}
	for torrent_hash in client.hashes() :
		for path in client.files(torrent_hash, system_path_flag) :
			files_dict.setdefault(path, set())
			files_dict[path].add(torrent_hash)
	return files_dict


###
def hashOrTorrent(method) :
	def wrap(self, torrent_hash, *args_list, **kwargs_dict) :
		if isinstance(torrent_hash, tfile.Torrent) :
			torrent_hash = torrent_hash.hash()
		return method(self, torrent_hash, *args_list, **kwargs_dict)
	return wrap

def loadTorrentAccessible(method) :
	def wrap(self, torrent, prefix = None) :
		torrent_path = torrent.path()
		open(torrent_path).close() # Check accessible file
		if not prefix is None :
			os.listdir(prefix) # Check accessible prefix
		return method(self, torrent, prefix)
	return wrap


##### Public classes #####
class AbstractClient(object) :
	def __init__(self, url) :
		object.__init__(self)
		assert isinstance(url, basestring)


	### Public ###

	@classmethod
	def plugin(cls) :
		raise NotImplementedError

	###

	@hashOrTorrent
	def removeTorrent(self, torrent_hash) :
		raise NotImplementedError

	@loadTorrentAccessible
	def loadTorrent(self, torrent, prefix = None) :
		raise NotImplementedError

	def hashes(self) :
		raise NotImplementedError

	@hashOrTorrent
	def hasTorrent(self, torrent_hash) :
		raise NotImplementedError

	@hashOrTorrent
	def torrentPath(self, torrent_hash) :
		raise NotImplementedError

	@hashOrTorrent
	def dataPrefix(self, torrent_hash) :
		raise NotImplementedError

	def defaultDataPrefix(self) :
		raise NotImplementedError

	###

	@classmethod
	def customKeys(cls) :
		return ()

	@hashOrTorrent
	def setCustoms(self, torrent_hash, customs_dict) :
		pass

	@hashOrTorrent
	def customs(self, torrent_hash, keys_list) :
		return {}

	###

	@hashOrTorrent
	def fullPath(self, torrent_hash) :
		raise NotImplementedError

	@hashOrTorrent
	def name(self, torrent_hash) :
		raise NotImplementedError

	@hashOrTorrent
	def isSingleFile(self, torrent_hash) :
		raise NotImplementedError

	@hashOrTorrent
	def files(self, torrent_hash, system_path_flag = False) :
		raise NotImplementedError

