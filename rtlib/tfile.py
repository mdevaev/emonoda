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
import copy
import bencode
import hashlib


##### Public methods #####
def torrents(src_dir_path) :
	torrents_dict = {}
	for torrent_file_name in filter(lambda name : name.endswith(".torrent"), os.listdir(src_dir_path)) :
		torrents_dict[torrent_file_name] = Torrent(os.path.join(src_dir_path, torrent_file_name))
	return torrents_dict

def torrentStruct(torrent_data) :
	return bencode.bdecode(torrent_data)


##### Public classes #####
class Torrent(object) :
	def __init__(self, torrent_file_path) :
		self.__torrent_file_path = torrent_file_path

		self.__bencode_dict = None
		self.__hash = None
		self.__scrape_hash = None

		self.load()


	### Public ###

	def load(self) :
		with open(self.__torrent_file_path) as torrent_file :
			self.__bencode_dict = torrentStruct(torrent_file.read())
			self.__hash = hashlib.sha1(bencode.bencode(self.__bencode_dict["info"])).hexdigest().lower()
			self.__scrape_hash = None

	###

	def comment(self) :
		return self.__bencode_dict.get("comment", "")

	def hash(self) :
		return self.__hash

	def scrapeHash(self) :
		if self.__scrape_hash is None :
			self.__scrape_hash = ""
			for index in xrange(0, len(self.__hash), 2) :
				self.__scrape_hash += "%{0}".format(self.__hash[index:index + 2])
		return self.__scrape_hash

