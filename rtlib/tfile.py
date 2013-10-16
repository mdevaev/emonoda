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


import sys
import os
import base64
import bencode
import hashlib
import urllib
import itertools


##### Public constants #####
ALL_MAGNET_FIELDS_TUPLE = ("dn", "tr", "xl")


##### Public methods #####
def torrents(src_dir_path, extension = ".torrent") :
	torrents_dict = {}
	for name in os.listdir(src_dir_path) :
		if not name.endswith(extension) :
			continue
		try :
			torrent = Torrent(os.path.join(src_dir_path, name))
		except bencode.BTL.BTFailure :
			torrent = None
		torrents_dict[name] = torrent
	return torrents_dict

def indexed(src_dir_path, prefix = "") :
	files_dict = {}
	for torrent in filter(None, torrents(src_dir_path).values()) :
		for path in torrent.files() :
			full_path = os.path.join(prefix, path)
			files_dict.setdefault(full_path, set())
			files_dict[full_path].add(torrent)
	return files_dict

def isValidTorrentData(data) :
	try :
		return isinstance(bencode.bdecode(data), dict) # Must be True
	except bencode.BTL.BTFailure :
		return False


###
def diff(old_torrent, new_torrent) :
	assert isinstance(old_torrent, (Torrent, dict))
	assert isinstance(new_torrent, (Torrent, dict))
	old_dict = ( old_torrent.files() if isinstance(old_torrent, Torrent) else old_torrent )
	new_dict = ( new_torrent.files() if isinstance(new_torrent, Torrent) else new_torrent )

	old_set = set(old_dict)
	new_set = set(new_dict)

	modified_set = set()
	modified_type_set = set()
	for path in old_set.intersection(new_set) :
		old_attrs_dict = old_dict[path]
		new_attrs_dict = new_dict[path]

		real = len(filter(None, (new_attrs_dict, old_attrs_dict)))
		if real == 0 :
			continue
		elif real == 1 :
			modified_type_set.add(path)
			continue

		#old_id_tuple = (old_attrs_dict["size"], old_attrs_dict["md5"])
		#new_id_tuple = (new_attrs_dict["size"], new_attrs_dict["md5"])
		#if old_id_tuple != new_id_tuple :
		if old_attrs_dict["size"] != new_attrs_dict["size"] :
			modified_set.add(path)

	return (
		new_set.difference(old_set), # Added
		old_set.difference(new_set), # Removed
		modified_set,
		modified_type_set,
	)

def printDiff(diff_tuple, prefix = "", output = sys.stdout) :
	(added_set, removed_set, modified_set, modified_type_set) = diff_tuple
	for (sign, files_set) in (
			("-", removed_set),
			("+", added_set),
			("~", modified_set),
			("?", modified_type_set),
		) :
		for item in sorted(files_set) :
			print >> output, "%s%s %s" % (prefix, sign, item)


###
def isSingleFile(bencode_dict) :
	return not bencode_dict["info"].has_key("files")

def torrentSize(bencode_dict) :
	if isSingleFile(bencode_dict) :
		return bencode_dict["info"]["length"]
	else :
		size = 0
		for file_dict in bencode_dict["info"]["files"] :
			size += file_dict["length"]
		return size

def torrentHash(bencode_dict) :
	return hashlib.sha1(bencode.bencode(bencode_dict["info"])).hexdigest().lower()


###
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

	magnet = "magnet:?xt=%s" % (urllib.quote_plus("urn:btih:%s" % (b32_hash)))
	if "dn" in extra_list :
		magnet += "&dn=" + urllib.quote_plus(bencode_dict["info"]["name"])
	if "tr" in extra_list :
		announce_list = bencode_dict.get("announce-list", [])
		if bencode_dict.has_key("announce") :
			announce_list.append([bencode_dict["announce"]])
		for announce in set(itertools.chain.from_iterable(announce_list)) :
			magnet += "&tr=" + urllib.quote_plus(announce)
	if "xl" in extra_list :
		magnet += "&xl=%d" % (torrentSize(bencode_dict))

	return magnet


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
		return self

	def loadData(self, data, torrent_file_path = None) :
		self.__initData(data)
		self.__torrent_file_path = torrent_file_path
		return self

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
		return isSingleFile(self.__bencode_dict)

	def files(self, prefix = "") :
		base = os.path.join(prefix, self.__bencode_dict["info"]["name"])
		if self.isSingleFile() :
			return { base : self.__fileAttrs(self.__bencode_dict["info"]) }
		else :
			files_dict = { base : None }
			for f_dict in self.__bencode_dict["info"]["files"] :
				name = None
				for index in xrange(len(f_dict["path"])) :
					name = os.path.join(base, os.path.sep.join(f_dict["path"][0:index + 1]))
					files_dict[name] = None
				assert not name is None
				files_dict[name] = self.__fileAttrs(f_dict)
			return files_dict

	def size(self) :
		return torrentSize(self.__bencode_dict)


	### Private ###

	def __initData(self, data) :
		self.__bencode_dict = bencode.bdecode(data)
		self.__hash = None
		self.__scrape_hash = None

	def __fileAttrs(self, file_dict) :
		return {
			"size" : file_dict["length"],
			"md5"  : file_dict.get("md5sum"),
		}

