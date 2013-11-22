#####
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


import urllib.parse
import http.cookiejar
import re

from .. import fetcherlib


##### Public constants #####
FETCHER_NAME = "rutracker"
FETCHER_VERSION = 1

RUTRACKER_DOMAIN = "rutracker.org"
RUTRACKER_URL = "http://%s" % (RUTRACKER_DOMAIN)
RUTRACKER_LOGIN_URL = "http://login.%s/forum/login.php" % (RUTRACKER_DOMAIN)
RUTRACKER_VIEWTOPIC_URL = "%s/forum/viewtopic.php" % (RUTRACKER_URL)
RUTRACKER_DL_URL = "http://dl.%s/forum/dl.php" % (RUTRACKER_DOMAIN)
RUTRACKER_ENCODING = "cp1251"


##### Public classes #####
class Fetcher(fetcherlib.AbstractFetcher) :
	def __init__(self, *args_tuple, **kwargs_dict) :
		self.__comment_regexp = re.compile(r"http://rutracker\.org/forum/viewtopic\.php\?t=(\d+)")

		self.__cap_static_regexp = re.compile(r"\"(http://static\.rutracker\.org/captcha/[^\"]+)\"")
		self.__cap_sid_regexp = re.compile(r"name=\"cap_sid\" value=\"([a-zA-Z0-9]+)\"")
		self.__cap_code_regexp = re.compile(r"name=\"(cap_code_[a-zA-Z0-9]+)\"")

		self.__hash_regexp = re.compile(r"<span id=\"tor-hash\">([a-zA-Z0-9]+)</span>")

		self.__cookie_jar = None
		self.__opener = None

		fetcherlib.AbstractFetcher.__init__(self, *args_tuple, **kwargs_dict)


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

	def ping(self) :
		opener = fetcherlib.buildTypicalOpener(proxy_url=self.proxyUrl())
		data = self.__readUrlRetry(RUTRACKER_URL, opener=opener).decode(RUTRACKER_ENCODING)
		self.assertSite("<link rel=\"shortcut icon\" href=\"http://static.%s/favicon.ico\" type=\"image/x-icon\">" % (RUTRACKER_DOMAIN) in data)

	def login(self) :
		self.assertNonAnonymous()
		self.__cookie_jar = http.cookiejar.CookieJar()
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
		return ( torrent.hash() != self.__fetchHash(torrent) )

	def fetchTorrent(self, torrent) :
		comment_match = self.__comment_regexp.match(torrent.comment() or "")
		self.assertFetcher(not comment_match is None, "No comment match")
		topic_id = comment_match.group(1)

		cookie = http.cookiejar.Cookie(
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

		data = self.__readUrlRetry(RUTRACKER_DL_URL+("?t=%s" % (topic_id)), b"", {
				"Referer"    : RUTRACKER_VIEWTOPIC_URL+("?t=%s" % (topic_id)),
				"Origin"     : "http://%s" % (RUTRACKER_DOMAIN),
			})
		self.assertValidTorrentData(data)
		return data


	### Private ###

	def __tryLogin(self) :
		post_dict = {
			"login_username" : self.userName(),#.decode("utf-8").encode("cp1251"),
			"login_password" : self.passwd(),#.decode("utf-8").encode("cp1251"),
			"login"          : "\xc2\xf5\xee\xe4",
		}
		post_data = urllib.parse.urlencode(post_dict).encode(RUTRACKER_ENCODING)
		data = self.__readUrlRetry(RUTRACKER_LOGIN_URL, post_data).decode(RUTRACKER_ENCODING)

		cap_static_match = self.__cap_static_regexp.search(data)
		if not cap_static_match is None :
			self.assertLogin(self.isInteractive(), "Required captcha")

			cap_sid_match = self.__cap_sid_regexp.search(data)
			cap_code_match = self.__cap_code_regexp.search(data)
			self.assertLogin(not cap_sid_match is None, "Unknown cap_sid")
			self.assertLogin(not cap_code_match is None, "Unknown cap_code")

			post_dict[cap_code_match.group(1)] = self.decodeCaptcha(cap_static_match.group(1))
			post_dict["cap_sid"] = cap_sid_match.group(1)
			post_data = urllib.parse.urlencode(post_dict).encode(RUTRACKER_ENCODING)
			data = self.__readUrlRetry(RUTRACKER_LOGIN_URL, post_data).decode(RUTRACKER_ENCODING)
			self.assertLogin(self.__cap_static_regexp.search(data) is None, "Invalid captcha or password")

	def __fetchHash(self, torrent) :
		data = self.__readUrlRetry(torrent.comment()).decode(RUTRACKER_ENCODING)
		hash_match = self.__hash_regexp.search(data)
		self.assertFetcher(not hash_match is None, "Hash not found")
		return hash_match.group(1).lower()

	def __readUrlRetry(self, url, data = None, headers_dict = None, opener = None) :
		opener = ( opener or self.__opener )
		assert not opener is None

		headers_dict = ( headers_dict or {} )
		user_agent = self.userAgent()
		if not user_agent is None :
			headers_dict.setdefault("User-Agent", user_agent)

		return fetcherlib.readUrlRetry(opener, url, data,
			headers_dict=headers_dict,
			timeout=self.timeout(),
			retries=self.urlRetries(),
			sleep_time=self.urlSleepTime(),
			retry_codes_list=(503, 404),
		)

