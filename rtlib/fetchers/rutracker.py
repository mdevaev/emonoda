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


from rtlib import const
from rtlib import fetcherlib

import urllib
import urllib2
import cookielib
import re


##### Public constants #####
FETCHER_NAME = "rutracker"
FETCHER_VERSION = 1

RUTRACKER_DOMAIN = "rutracker.org"
RUTRACKER_LOGIN_URL = "http://login.%s/forum/login.php" % (RUTRACKER_DOMAIN)
RUTRACKER_VIEWTOPIC_URL = "http://%s/forum/viewtopic.php" % (RUTRACKER_DOMAIN)
RUTRACKER_DL_URL = "http://dl.%s/forum/dl.php" % (RUTRACKER_DOMAIN)


##### Public classes #####
class Fetcher(fetcherlib.AbstractFetcher) :
	def __init__(self, user_name, passwd, url_retries, url_sleep_time, proxy_url, interactive_flag) :
		fetcherlib.AbstractFetcher.__init__(self, user_name, passwd, url_retries, url_sleep_time, proxy_url, interactive_flag)

		self.__user_name = user_name
		self.__passwd = passwd
		self.__url_retries = url_retries
		self.__url_sleep_time = url_sleep_time
		self.__proxy_url = proxy_url
		self.__interactive_flag = interactive_flag

		self.__comment_regexp = re.compile(r"http://rutracker\.org/forum/viewtopic\.php\?t=(\d+)")

		self.__cap_static_regexp = re.compile(r"\"(http://static\.rutracker\.org/captcha/[^\"]+)\"")
		self.__cap_sid_regexp = re.compile(r"name=\"cap_sid\" value=\"([a-zA-Z0-9]+)\"")
		self.__cap_code_regexp = re.compile(r"name=\"(cap_code_[a-zA-Z0-9]+)\"")

		self.__hash_regexp = re.compile(r"<span id=\"tor-hash\">([a-zA-Z0-9]+)</span>")

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
		self.assertNonAnonymous(self.__user_name)
		self.__cookie_jar = cookielib.CookieJar()
		self.__opener = fetcherlib.buildTypicalOpener(self.__cookie_jar, self.__proxy_url)
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
		return ( torrent.hash() != self.__fetchHash(torrent) )

	def fetchTorrent(self, torrent) :
		comment_match = self.__comment_regexp.match(torrent.comment() or "")
		self.assertFetcher(not comment_match is None, "No comment match")
		topic_id = comment_match.group(1)

		cookie = cookielib.Cookie(
			version=0,
			name="bb_dl",
			value=topic_id,
			port=None,
			port_specified=False,
			domain="",
			domain_specified=False,
			domain_initial_dot=False,
			path="/forum/",
			path_specified=True,
			secure=False,
			expires=None,
			discard=True,
			comment=None,
			comment_url=None,
			rest={ "HttpOnly" : None },
			rfc2109=False,
		)
		self.__cookie_jar.set_cookie(cookie)
		request = urllib2.Request(RUTRACKER_DL_URL+("?t=%s" % (topic_id)), "", headers={
				"Referer" : RUTRACKER_VIEWTOPIC_URL+("?t=%s" % (topic_id)),
				"Origin" : "http://%s" % (RUTRACKER_DOMAIN),
				"User-Agent" : const.BROWSER_USER_AGENT,
			})

		data = self.__readUrlRetry(request)
		self.assertValidTorrentData(data)
		return data


	### Private ###

	def __tryLogin(self) :
		post_dict = {
			"login_username" : self.__user_name.decode("utf-8").encode("cp1251"),
			"login_password" : self.__passwd.decode("utf-8").encode("cp1251"),
			"login" : "\xc2\xf5\xee\xe4",
		}
		data = self.__readUrlRetry(RUTRACKER_LOGIN_URL, urllib.urlencode(post_dict))

		cap_static_match = self.__cap_static_regexp.search(data)
		if not cap_static_match is None :
			self.assertLogin(self.__interactive_flag, "Required captcha")

			cap_sid_match = self.__cap_sid_regexp.search(data)
			cap_code_match = self.__cap_code_regexp.search(data)
			self.assertLogin(not cap_sid_match is None, "Unknown cap_sid")
			self.assertLogin(not cap_code_match is None, "Unknown cap_code")

			print ":: Enter the capthca [ %s ]:" % (cap_static_match.group(1)),
			post_dict[cap_code_match.group(1)] = raw_input()
			post_dict["cap_sid"] = cap_sid_match.group(1)
			data = self.__readUrlRetry(RUTRACKER_LOGIN_URL, urllib.urlencode(post_dict))
			self.assertLogin(self.__cap_static_regexp.search(data) is None, "Invalid captcha or password")

	def __fetchHash(self, torrent) :
		data = self.__readUrlRetry(torrent.comment())
		hash_match = self.__hash_regexp.search(data)
		self.assertFetcher(not hash_match is None, "Hash not found")
		return hash_match.group(1).lower()

	def __readUrlRetry(self, *args_list, **kwargs_dict) :
		kwargs_dict.setdefault("opener", self.__opener)
		kwargs_dict.setdefault("retry_codes_list", (503, 404))
		kwargs_dict["retries"] = self.__url_retries
		kwargs_dict["sleep_time"] = self.__url_sleep_time
		return fetcherlib.readUrlRetry(*args_list, **kwargs_dict)

