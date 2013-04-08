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
import bencode
import hashlib


##### Public methods #####
def torrents(src_dir_path, extension = ".torrent") :
	return dict([
			(name, Torrent(os.path.join(src_dir_path, name)))
			for name in os.listdir(src_dir_path)
			if name.endswith(extension)
		])

def torrentStruct(t_data) :
	return bencode.bdecode(t_data)

def torrentHash(bencode_dict) :
	return hashlib.sha1(bencode.bencode(bencode_dict["info"])).hexdigest().lower()

def scrapeHash(torrent_hash) :
	scrape_hash = ""
	for index in xrange(0, len(torrent_hash), 2) :
		scrape_hash += "%{0}".format(torrent_hash[index:index + 2])
	return scrape_hash


##### Public classes #####
class Torrent(object) :
	def __init__(self, torrent_file_path) :
		self.__torrent_file_path = torrent_file_path

		self.__bencode_dict = None
		self.__hash = None
		self.__scrape_hash = None

		self.reload()


	### Public ###

	def reload(self) :
		with open(self.__torrent_file_path) as torrent_file :
			self.__bencode_dict = torrentStruct(torrent_file.read())
			self.__hash = None
			self.__scrape_hash = None

	###

	def path(self) :
		return self.__torrent_file_path

	def bencode(self) :
		return self.__bencode_dict

	def comment(self) :
		return self.__bencode_dict.get("comment", "")

	def hash(self) :
		if self.__hash is None :
			self.__hash = torrentHash(self.__bencode_dict)
		return self.__hash

	def scrapeHash(self) :
		if self.__scrape_hash is None :
			self.__scrape_hash = scrapeHash(self.__hash)
		return self.__scrape_hash

	def files(self, prefix = "") :
		# XXX: See https://wiki.theory.org/BitTorrentSpecification for details
		base = os.path.join(prefix, self.__bencode_dict["info"]["name"])
		if not self.__bencode_dict["info"].has_key("files") : # Single File Mode
			return [base]
		else : # Multiple File Mode
			files_list = [base]
			for file_dict in self.__bencode_dict["info"]["files"] :
				for (index, _) in enumerate(file_dict["path"]) :
					files_list.append(os.path.join(prefix, base, os.path.sep.join(file_dict["path"][0:index + 1])))
			return files_list

