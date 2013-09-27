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
import base64
import bencode
import hashlib
import urllib


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

def makeMagnet(bencode_dict, extra_list = None) :
	# XXX: http://stackoverflow.com/questions/12479570/given-a-torrent-file-how-do-i-generate-a-magnet-link-in-python
	info_sha1 = hashlib.sha1(bencode.bencode(bencode_dict["info"]))
	info_digest = info_sha1.digest() # pylint: disable=E1121
	b32_hash = base64.b32encode(info_digest)
	args_dict = {
		"xt" : "urn:btih:%s" % (b32_hash),
		"dn" : bencode_dict["info"]["name"],
		"tr" : bencode_dict["announce"],
		#"xl" : bencode_dict["info"]["length"],
	}
	for key in set(args_dict).difference(tuple(extra_list or ()) + ("xt",)) :
		args_dict.pop(key)
	return "magnet:?" + urllib.urlencode(args_dict)


##### Public classes #####
class Torrent(object) :
	def __init__(self, torrent_file_path = None) :
		# XXX: File format: https://wiki.theory.org/BitTorrentSpecification

		self.__torrent_file_path = None
		self.__bencode_dict = None
		self.__hash = None
		self.__scrape_hash = None

		if not torrent_file_path is None :
			self.loadFile(torrent_file_path)


	### Public ###

	def loadFile(self, torrent_file_path) :
		with open(torrent_file_path) as torrent_file :
			self.loadData(torrent_file.read(), torrent_file_path)

	def loadData(self, data, torrent_file_path = None) :
		self.initData(data)
		self.__torrent_file_path = torrent_file_path

	###

	def path(self) :
		return self.__torrent_file_path

	def bencode(self) :
		return self.__bencode_dict

	###

	def name(self) :
		return self.__bencode_dict["info"]["name"]

	def comment(self) :
		return self.__bencode_dict.get("comment")

	def creationDate(self) :
		return self.__bencode_dict.get("creation date")

	def createdBy(self) :
		return self.__bencode_dict.get("created by")

	def announce(self) :
		return self.__bencode_dict.get("announce")

	def announceList(self) :
		return self.__bencode_dict.get("announce-list", [])

	def isPrivate(self) :
		return bool(self.__bencode_dict["info"].get("private", 0))

	###

	def hash(self) :
		if self.__hash is None :
			self.__hash = torrentHash(self.__bencode_dict)
		return self.__hash

	def scrapeHash(self) :
		if self.__scrape_hash is None :
			self.__scrape_hash = scrapeHash(self.hash())
		return self.__scrape_hash

	###

	def magnet(self, extra_list) :
		return makeMagnet(self.__bencode_dict, extra_list)

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

	def size(self) :
		if self.isSingleFile() :
			return self.__bencode_dict["info"]["length"]
		else :
			size = 0
			for file_dict in self.__bencode_dict["info"]["files"] :
				size += file_dict["length"]
			return size


	### Private ###

	def initData(self, data) :
		self.__bencode_dict = torrentStruct(data)
		self.__hash = None
		self.__scrape_hash = None

