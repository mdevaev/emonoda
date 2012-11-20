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


from rtlib import fetcher
from rtlib import torrents

import urllib
import urllib2
import cookielib
import bencode
import re


##### Public constants #####
NNMCLUB_DOMAIN = "nnm-club.ru"
NNMCLUB_LOGIN_URL = "http://%s/forum/login.php" % (NNMCLUB_DOMAIN)
#NNMCLUB_VIEWTOPIC_URL = "http://%s/forum/viewtopic.php" % (NNMCLUB_DOMAIN)
NNMCLUB_DL_URL = "http://%s/forum/download.php" % (NNMCLUB_DOMAIN)
NNMCLUB_SCRAPE_URL = "http://%s:2710/scrape" % (NNMCLUB_DOMAIN)


##### Public classes #####
class Fetcher(fetcher.AbstractFetcher) :
	def __init__(self, user_name, passwd, interactive_flag = False) :
		fetcher.AbstractFetcher.__init__(self, user_name, passwd, interactive_flag)

		self.__user_name = user_name
		self.__passwd = passwd
		self.__interactive_flag = interactive_flag

		self.__comment_regexp = re.compile(r"http://nnm-club\.ru/forum/viewtopic\.php\?p=(\d+)")
		self.__torrent_id_regexp = re.compile(r"filelst.php\?attach_id=([a-zA-Z0-9]+)")

		self.__cookie_jar = None
		self.__opener = None


	### Public ###

	@classmethod
	def name(self) :
		return "nnm-club"

	def match(self, bencode_dict) :
		return ( not self.__comment_regexp.match(bencode_dict["comment"]) is None )

	def login(self) :
		cookie_jar = cookielib.CookieJar()
		opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.__cookie_jar))

		post_dict = {
			"username" : self.__user_name,
			"password" : self.__passwd,
			"redirect" : "",
			"login" : "%C2%F5%EE%E4"
		}
		data = opener.open(NNMCLUB_LOGIN_URL, urllib.urlencode(post_dict)).read()
		if not "[ %s ]" % (self.__user_name) in data :
			raise RuntimeError("Invalid login")

		self.__cookie_jar = cookie_jar
		self.__opener = opener

	def loggedIn(self) :
		return ( not self.__opener is None )

	def torrentChanged(self, bencode_dict) :
		torrent_hash = torrents.torrentHash(bencode_dict)
		scrape_hash = torrents.scrapeHash(torrent_hash)
		data = self.__opener.open(NNMCLUB_SCRAPE_URL+("?info_hash=%s" % (scrape_hash))).read()
		if not data.startswith("d5:") :
			raise RuntimeError("Invalid scrape answer")
		return ( data.strip() == "d5:filesdee" )

	def fetchTorrent(self, bencode_dict) :
		data = self.__opener.open(bencode_dict["comment"]).read()
		torrent_id_match = self.__torrent_id_regexp.search(data)
		assert not torrent_id_match is None, "Unknown torrent_id"
		torrent_id = torrent_id_match.group(1)
		data = self.__opener.open(NNMCLUB_DL_URL+("?id=%s" % (torrent_id))).read()
		bencode.bdecode(data)
		return data

