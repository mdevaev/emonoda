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
def torrents(src_dir_path) :
	torrents_dict = {}
	for torrent_file_name in filter(lambda name : name.endswith(".torrent"), os.listdir(src_dir_path)) :
		with open(os.path.join(src_dir_path, torrent_file_name)) as torrent_file :
			bencode_dict = bencode.bdecode(torrent_file.read())
			bencode_dict.setdefault("comment", "")
			torrents_dict[torrent_file_name] = bencode_dict
	return torrents_dict

def torrentHash(bencode_dict) :
	return hashlib.sha1(bencode.bencode(bencode_dict["info"])).hexdigest().upper()

def scrapeHash(torrent_hash) :
	scrape_hash = ""
	for index in xrange(0, len(torrent_hash), 2) :
		scrape_hash += "%{0}".format(torrent_hash[index:index + 2])
	return scrape_hash

