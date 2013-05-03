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


import tfile


##### Public methods #####
def indexed(client, system_path_flag = False) :
	files_dict = {}
	for torrent_hash in client.hashs() :
		for path in client.files(torrent_hash, system_path_flag) :
			files_dict.setdefault(path, set())
			files_dict[path].add(torrent_hash)
	return files_dict


###
def maybeHash(item, required_torrent_flag = True) :
	if required_torrent_flag :
		assert isinstance(item, tfile.Torrent), "Required instance of the %s" % (str(tfile.Torrent))
		return item.hash()
	else :
		if isinstance(item, tfile.Torrent) :
			return item.hash()
		else :
			assert isinstance(item, (str, unicode)), "Required string hash"
			return item


##### Public classes #####
class AbstractClient(object) :
	def __init__(self, url) :
		self.__url = url
		object.__init__(self)


	### Public ###

	@classmethod
	def plugin(self) :
		raise NotImplementedError

	###

	def removeTorrent(self, torrent) :
		raise NotImplementedError

	def loadTorrent(self, torrent) :
		raise NotImplementedError

	def hashs(self) :
		raise NotImplementedError

	def torrentPath(self, torrent) :
		raise NotImplementedError

	###

	def setCustom(self, index, torrent, data) :
		raise NotImplementedError

	def custom(self, index, torrent) :
		raise NotImplementedError

	###

	def fullPath(self, torrent) :
		raise NotImplementedError

	def name(self, torrent) :
		raise NotImplementedError

	def isSingleFile(self, torrent) :
		raise NotImplementedError

	def files(self, torrent, system_path_flag = False) :
		raise NotImplementedError

