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


##### Public classes #####
class AbstractFetcher(object) :
	def __init__(self, user_name, passwd, interactive_flag = False) :
		object.__init__(self)

	@classmethod
	def name(self) :
		raise NotImplementedError

	def match(self, bencode_dict) :
		raise NotImplementedError

	def login(self) :
		raise NotImplementedError

	def loggedIn(self) :
		raise NotImplementedError

	def torrentChanged(self, bencode_dict) :
		raise NotImplementedError

	def fetchTorrent(self, bencode_dict) :
		raise NotImplementedError

