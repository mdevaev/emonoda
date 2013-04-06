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
from rtlib import tfile

import urllib
import urllib2
import socket
import cookielib
import json
import time
import re


##### Public constants #####
RUTRACKER_DOMAIN = "rutracker.org"
RUTRACKER_LOGIN_URL = "http://login.%s/forum/login.php" % (RUTRACKER_DOMAIN)
RUTRACKER_VIEWTOPIC_URL = "http://%s/forum/viewtopic.php" % (RUTRACKER_DOMAIN)
RUTRACKER_DL_URL = "http://dl.%s/forum/dl.php" % (RUTRACKER_DOMAIN)
RUTRACKER_AJAX_URL = "http://%s/forum/ajax.php" % (RUTRACKER_DOMAIN)


##### Public classes #####
class Fetcher(fetcherlib.AbstractFetcher) :
	def __init__(self, user_name, passwd, interactive_flag = False) :
		fetcherlib.AbstractFetcher.__init__(self, user_name, passwd, interactive_flag)

		self.__user_name = user_name
		self.__passwd = passwd
		self.__interactive_flag = interactive_flag

		self.__comment_regexp = re.compile(r"http://rutracker\.org/forum/viewtopic\.php\?t=(\d+)")

		self.__cap_static_regexp = re.compile(r"\"(http://static\.rutracker\.org/captcha/[^\"]+)\"")
		self.__cap_sid_regexp = re.compile(r"name=\"cap_sid\" value=\"([a-zA-Z0-9]+)\"")
		self.__cap_code_regexp = re.compile(r"name=\"(cap_code_[a-zA-Z0-9]+)\"")

		self.__hash_t_regexp = re.compile(r"t_hash\s*:\s*'([a-zA-Z0-9]+)'")
		self.__hash_form_token_regexp = re.compile(r"name=\"form_token\" value=\"([a-zA-Z0-9]+)\"")

		self.__cookie_jar = None
		self.__opener = None


	### Public ###

	@classmethod
	def name(self) :
		return "rutracker"

	def match(self, torrent) :
		return ( not self.__comment_regexp.match(torrent.comment()) is None )

	def login(self) :
		self.__cookie_jar = cookielib.CookieJar()
		self.__opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.__cookie_jar))
		try :
			self.tryLogin()
		except :
			self.__cookie_jar = None
			self.__opener = None
			raise

	def loggedIn(self) :
		return ( not self.__opener is None )

	def torrentChanged(self, torrent) :
		return ( torrent.hash() != self.fetchHash(torrent) )

	def fetchTorrent(self, torrent) :
		comment_match = self.__comment_regexp.match(torrent.comment())
		assert not comment_match is None, "No comment match"
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

		data = self.readUrlRetry(request)
		tfile.torrentStruct(data)
		return data


	### Private ###

	def tryLogin(self) :
		post_dict = {
			"login_username" : self.__user_name,
			"login_password" : self.__passwd,
			"login" : "\xc2\xf5\xee\xe4",
		}
		data = self.readUrlRetry(RUTRACKER_LOGIN_URL, urllib.urlencode(post_dict))

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
			web_file = self.readUrlRetry(RUTRACKER_LOGIN_URL, urllib.urlencode(post_dict))
			self.assertLogin(self.__cap_static_regexp.search(web_file.read()) is None, "Invalid captcha")

	def fetchHash(self, torrent) :
		comment_match = self.__comment_regexp.match(torrent.comment())
		assert not comment_match is None, "No comment match"

		data = self.readUrlRetry(torrent.comment())
		hash_t_match = self.__hash_t_regexp.search(data)
		hash_form_token_match = self.__hash_form_token_regexp.search(data)
		self.assertFetcher(not hash_t_match is None, "Unknown t_hash")
		self.assertFetcher(not hash_form_token_match is None, "Unknown form_token")

		post_dict = {
			"action" : "get_info_hash",
			"topic_id" : comment_match.group(1),
			"t_hash" : hash_t_match.group(1),
			"form_token" : hash_form_token_match.group(1),
		}
		request = urllib2.Request(RUTRACKER_AJAX_URL, urllib.urlencode(post_dict), headers={
				"User-Agent" : const.BROWSER_USER_AGENT
			})
		response_dict = json.loads(self.readUrlRetry(request))
		if response_dict.has_key("ih_hex") :
			return response_dict["ih_hex"].lower()
		elif response_dict.has_key("error_msg") : # Like self.assertFetcher()
			raise fetcherlib.FetcherError(unicode(response_dict["error_msg"]).encode("utf-8"))
		else :
			raise fetcherlib.FetcherError("Invalid response: %s" % (str(response_dict)))

	def readUrlRetry(self, *args_list, **kwargs_dict) :
		kwargs_dict.setdefault("opener", self.__opener)
		kwargs_dict.setdefault("retry_codes_list", (503, 404))
		return fetcherlib.readUrlRetry(*args_list, **kwargs_dict)

