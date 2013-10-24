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

import urllib
import cookielib
import re


##### Public constants #####
FETCHER_NAME = "nnm-club"
FETCHER_VERSION = 1

NNMCLUB_DOMAIN = "nnm-club.me"
NNMCLUB_LOGIN_URL = "http://%s/forum/login.php" % (NNMCLUB_DOMAIN)
NNMCLUB_DL_URL = "http://%s/forum/download.php" % (NNMCLUB_DOMAIN)
NNMCLUB_SCRAPE_URL = "http://bt.%s:2710/scrape" % (NNMCLUB_DOMAIN)
REPLACE_DOMAINS = ("nnm-club.ru", "nnm-club.me")


##### Public classes #####
class Fetcher(fetcherlib.AbstractFetcher) :
	def __init__(self, *args_tuple, **kwargs_dict) :
		fetcherlib.AbstractFetcher.__init__(self, *args_tuple, **kwargs_dict)

		self.__comment_regexp = re.compile(r"http://nnm-club\.(me|ru)/forum/viewtopic\.php\?p=(\d+)")
		self.__torrent_id_regexp = re.compile(r"filelst.php\?attach_id=([a-zA-Z0-9]+)")

		self.__cookie_jar = None
		self.__opener = None


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
		self.assertNonAnonymous()
		self.__cookie_jar = cookielib.CookieJar()
		self.__opener = fetcherlib.buildTypicalOpener(self.__cookie_jar, self.proxyUrl())
		try :
			self.__tryLogin()
		except :
			self.__cookie_jar = None
			self.__opener = None
			raise

	def loggedIn(self) :
		return ( not self.__opener is None )

	def torrentChanged(self, torrent) :
		self.assertMatch(torrent)
		client_agent = self.clientAgent()
		headers_dict = ( { "User-Agent" : client_agent } if not client_agent is None else None )
		data = self.__readUrlRetry(NNMCLUB_SCRAPE_URL+("?info_hash=%s" % (torrent.scrapeHash())), headers_dict=headers_dict)
		self.assertFetcher(data.startswith("d5:"), "Invalid scrape answer")
		return ( data.strip() == "d5:filesdee" )

	def fetchTorrent(self, torrent) :
		self.assertMatch(torrent)
		data = self.__readUrlRetry(torrent.comment().replace(*REPLACE_DOMAINS))

		torrent_id_match = self.__torrent_id_regexp.search(data)
		self.assertFetcher(not torrent_id_match is None, "Unknown torrent_id")
		torrent_id = torrent_id_match.group(1)

		data = self.__readUrlRetry(NNMCLUB_DL_URL+("?id=%s" % (torrent_id)))
		self.assertValidTorrentData(data)
		return data


	### Private ###

	def __tryLogin(self) :
		post_dict = {
			"username" : self.userName(),
			"password" : self.passwd(),
			"redirect" : "",
			"login"    : "\xc2\xf5\xee\xe4",
		}
		data = self.__readUrlRetry(NNMCLUB_LOGIN_URL, urllib.urlencode(post_dict))
		self.assertLogin("[ %s ]" % (self.userName()) in data, "Invalid login")

	def __readUrlRetry(self, url, data = None, headers_dict = None) :
		headers_dict = ( headers_dict or {} )
		user_agent = self.userAgent()
		if not user_agent is None :
			headers_dict.setdefault("User-Agent", user_agent)
		return fetcherlib.readUrlRetry(self.__opener, url, data,
			headers_dict=headers_dict,
			retries=self.urlRetries(),
			sleep_time=self.urlSleepTime(),
		)

