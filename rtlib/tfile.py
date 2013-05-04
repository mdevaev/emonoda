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

def indexed(src_dir_path, prefix = "") :
	files_dict = {}
	for torrent in torrents(src_dir_path).values() :
		for path in torrent.files() :
			full_path = os.path.join(prefix, path)
			files_dict.setdefault(full_path, set())
			files_dict[full_path].add(torrent)
	return files_dict

def diff(old_torrent, new_torrent) :
	old_set = old_torrent.files()
	new_set = new_torrent.files()
	return (
		new_set.difference(old_set), # Added
		old_set.difference(new_set), # Removed
	)


###
def torrentStruct(torrent_data) :
	return bencode.bdecode(torrent_data)


###
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
		# XXX: File format: https://wiki.theory.org/BitTorrentSpecification

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

	def name(self) :
		return self.__bencode_dict["info"]["name"]

	def comment(self) :
		return self.__bencode_dict.get("comment", "")

	def hash(self) :
		if self.__hash is None :
			self.__hash = torrentHash(self.__bencode_dict)
		return self.__hash

	def scrapeHash(self) :
		if self.__scrape_hash is None :
			self.__scrape_hash = scrapeHash(self.hash())
		return self.__scrape_hash

	###

	def isSingleFile(self) :
		return not self.__bencode_dict["info"].has_key("files")

	def files(self, prefix = "") :
		base = os.path.join(prefix, self.__bencode_dict["info"]["name"])
		files_set = set([base]) # Single File Mode
		if not self.isSingleFile() : # Multiple File Mode
			for file_dict in self.__bencode_dict["info"]["files"] :
				for index in xrange(len(file_dict["path"])) :
					files_set.add(os.path.join(base, os.path.sep.join(file_dict["path"][0:index + 1])))
		return files_set

