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


##### Public classes #####
class RTorrent(object) :
	# XXX: API description: http://code.google.com/p/gi-torrent/wiki/rTorrent_XMLRPC_reference

	def __init__(self, url) :
		self.__server = xmlrpclib.ServerProxy(url)

	def removeTorrent(self, torrent) :
		self.__server.d.erase(torrent.hash())

	def loadTorrent(self, torrent) :
		self.__server.load_start(torrent.path())

	###

	def setCustom(self, index, torrent, data) :
		assert 1 <= index <= 5, "Invalid custom index"
		method = getattr(self.__server.d, "set_custom%d" % (index))
		method(torrent.hash(), data)

	def custom(self, index, torrent) :
		assert 1 <= index <= 5, "Invalid custom index"
		method = getattr(self.__server.d, "get_custom%d" % (index))
		return method(torrent.hash())

