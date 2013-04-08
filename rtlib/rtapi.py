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


import xmlrpclib

import tfile


##### Public classes #####
class RTorrent(object) :
	# XXX: API description: http://code.google.com/p/gi-torrent/wiki/rTorrent_XMLRPC_reference

	def __init__(self, url) :
		self.__server = xmlrpclib.ServerProxy(url)


	### Public ###

	def removeTorrent(self, torrent) :
		self.__server.d.erase(self.maybeHash(torrent, False))

	def loadTorrent(self, torrent) :
		self.maybeHash(torrent)
		self.__server.load_start(torrent.path())

	###

	def setCustom(self, index, torrent, data) :
		assert 1 <= index <= 5, "Invalid custom index"
		method = getattr(self.__server.d, "set_custom%d" % (index))
		method(self.maybeHash(torrent, False), data)

	def custom(self, index, torrent) :
		assert 1 <= index <= 5, "Invalid custom index"
		method = getattr(self.__server.d, "get_custom%d" % (index))
		return method(self.maybeHash(torrent, False))

	def fullPath(self, torrent) :
		return self.__server.d.get_base_path(self.maybeHash(torrent, False))

	###

	def hashs(self) :
		return self.__server.download_list()


	### Private ###

	def maybeHash(self, item, required_torrent_flag = True) :
		if required_torrent_flag :
			assert isinstance(item, tfile.Torrent), "Required instance of the %s" % (str(tfile.Torrent))
			return item.hash()
		else :
			if isinstance(item, tfile.Torrent) :
				return item.hash()
			else :
				assert isinstance(item, (str, unicode)), "Required string hash"
				return item

