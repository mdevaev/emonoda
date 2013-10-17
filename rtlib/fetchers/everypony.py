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


from rtlib import fetcherlib

import re


##### Public constants #####
FETCHER_NAME = "everypony"
FETCHER_VERSION = 0


##### Public classes #####
class Fetcher(fetcherlib.AbstractFetcher) :
	def __init__(self, user_name, passwd, url_retries, url_sleep_time, proxy_url, interactive_flag) :
		fetcherlib.AbstractFetcher.__init__(self, user_name, passwd, url_retries, url_sleep_time, proxy_url, interactive_flag)

		self.__url_retries = url_retries
		self.__url_sleep_time = url_sleep_time
		self.__proxy_url = proxy_url

		self.__comment_regexp = re.compile(r"http://tabun\.everypony\.ru/blog/torrents/\d+\.html")
		self.__hash_regexp = re.compile(r"<blockquote>\s*Hash\s*:\s*([a-fA-F0-9]{40})\s*<br/>")
		self.__dl_regexp = re.compile(r"Torrent\s*:\s*<a href=\"(http://[^\"]+)\"")

		self.__opener = None
		self.__last_hash = None
		self.__last_page = None


	### Public ###

	@classmethod
	def plugin(cls) :
		return FETCHER_NAME

	@classmethod
	def version(cls) :
		return FETCHER_VERSION

	###

	def match(self, torrent) :
		return ( not self.__comment_regexp.match(torrent.comment() or "") is None )

	def login(self) :
		self.__opener = fetcherlib.buildTypicalOpener(proxy_url=self.__proxy_url)

	def loggedIn(self) :
		return True

	def torrentChanged(self, torrent) :
		self.assertMatch(torrent)
		return ( torrent.hash() != self.__fetchHash(torrent) )


	def fetchTorrent(self, torrent) :
		self.assertMatch(torrent)
		self.__loadPage(torrent)
		dl_match = self.__dl_regexp.search(self.__last_page)
		self.assertFetcher(not dl_match is None, "Download not found")
		data = self.__readUrlRetry(dl_match.group(1))
		self.assertValidTorrentData(data)
		return data


	### Private ###

	def __loadPage(self, torrent) :
		torrent_hash = torrent.hash()
		if self.__last_hash != torrent_hash :
			self.__last_page = self.__readUrlRetry(torrent.comment())
			self.__last_hash = torrent_hash

	def __fetchHash(self, torrent) :
		self.__loadPage(torrent)
		hash_match = self.__hash_regexp.search(self.__last_page)
		self.assertFetcher(not hash_match is None, "Hash not found")
		return hash_match.group(1).lower()

	def __readUrlRetry(self, *args_list, **kwargs_dict) :
		kwargs_dict.setdefault("opener", self.__opener)
		kwargs_dict["retries"] = self.__url_retries
		kwargs_dict["sleep_time"] = self.__url_sleep_time
		return fetcherlib.readUrlRetry(*args_list, **kwargs_dict)

