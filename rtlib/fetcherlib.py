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


import const
import tfile

import ulib.tools.coding
import ulib.tools.url

import socket
import urllib2
import urlparse
import types
import json
import time


##### Public constants #####
DEFAULT_LOGIN = ""
DEFAULT_PASSWD = ""
DEFAULT_URL_RETRIES = 10
DEFAULT_URL_SLEEP_TIME = 1
DEFAULT_PROXY_URL = None
DEFAULT_INTERACTIVE_FLAG = False

VERSIONS_URL = const.RAW_UPSTREAM_URL + "/fetchers.json"


##### Exceptions #####
class CommonFetcherError(Exception) :
	pass

class LoginError(CommonFetcherError) :
	pass

class FetcherError(CommonFetcherError) :
	pass


##### Public methods #####
def selectFetcher(torrent, fetchers_list) :
	for fetcher in fetchers_list :
		if fetcher.match(torrent) :
			return fetcher
	return None


###
def buildTypicalOpener(cookie_jar = None, proxy_url = None) :
	handlers_list = []
	if not cookie_jar is None :
		handlers_list.append(urllib2.HTTPCookieProcessor(cookie_jar))
	if not proxy_url is None :
		scheme = ( urlparse.urlparse(proxy_url).scheme or "" ).lower()
		if scheme == "http" :
			handlers_list.append(urllib2.ProxyHandler({
					"http"  : proxy_url,
					"https" : proxy_url,
				}))
		elif scheme in ("socks4", "socks5") :
			handlers_list.append(ulib.tools.url.SocksHandler(proxy_url=proxy_url))
		else :
			raise RuntimeError("Invalid proxy protocol: %s" % (scheme))
	return urllib2.build_opener(*handlers_list)

def readUrlRetry(*args_list, **kwargs_dict) :
	opener = kwargs_dict.pop("opener", None)
	if opener is None :
		opener = urllib2.build_opener()
	retries = kwargs_dict.pop("retries", DEFAULT_URL_RETRIES)
	sleep_time = kwargs_dict.pop("sleep_time", DEFAULT_URL_SLEEP_TIME)
	retry_codes_list = kwargs_dict.pop("retry_codes_list", (503, 502, 500))
	retry_timeout_flag = kwargs_dict.pop("retry_timeout_flag", True)

	while True :
		try :
			return opener.open(*args_list, **kwargs_dict).read()
		except (socket.timeout, urllib2.URLError, urllib2.HTTPError), err :
			if retries == 0 :
				raise
			if isinstance(err, socket.timeout) or isinstance(err, urllib2.URLError) and err.reason == "timed out" :
				if not retry_timeout_flag :
					raise
			elif isinstance(err, urllib2.HTTPError) :
				if not err.code in retry_codes_list :
					raise
			retries -= 1
			time.sleep(sleep_time)


###
def checkVersions(fetchers_list) :
	versions_dict = json.loads(urllib2.urlopen(VERSIONS_URL).read())
	ok_flag = True
	for fetcher in fetchers_list :
		plugin_name = fetcher.plugin()
		local_version = fetcher.version()
		if not versions_dict.has_key(plugin_name) :
			continue
		upstream_version = versions_dict[plugin_name]["version"]
		if local_version < upstream_version :
			print "# Plug-in \"%s\" is outdated." % (plugin_name)
			print "#    Local version:    %d" % (local_version)
			print "#    Upstream version: %d" % (upstream_version)
			print "# The plugin can not work properly. It is recommended to upgrade the program."
			ok_flag = False
	return ok_flag


##### Public classes #####
class AbstractFetcher(object) :
	def __init__(self, user_name, passwd, url_retries, url_sleep_time, proxy_url, interactive_flag) :
		object.__init__(self)
		assert isinstance(user_name, basestring)
		assert isinstance(passwd, basestring)
		assert isinstance(url_retries, (int, long))
		assert isinstance(url_sleep_time, (int, long))
		assert isinstance(proxy_url, (basestring, types.NoneType))
		assert isinstance(interactive_flag, bool)


	### Public ###

	@classmethod
	def plugin(cls) :
		raise NotImplementedError

	@classmethod
	def version(cls) :
		raise NotImplementedError

	###

	def match(self, torrent) :
		raise NotImplementedError

	def login(self) :
		raise NotImplementedError

	def loggedIn(self) :
		raise NotImplementedError

	def torrentChanged(self, torrent) :
		raise NotImplementedError

	def fetchTorrent(self, torrent) :
		raise NotImplementedError

	###

	def assertLogin(self, *args_list) :
		self.__customAssert(LoginError, *args_list)

	def assertFetcher(self, *args_list) :
		self.__customAssert(FetcherError, *args_list)

	###

	def assertNonAnonymous(self, login) :
		self.assertLogin(len(login) != 0, "The tracker \"%s\" can not be used anonymously" % (self.plugin()))

	def assertMatch(self, torrent) :
		self.assertFetcher(self.match(torrent), "No comment match")

	def assertValidTorrentData(self, data) :
		message = "Received an invalid torrent data: %s ..." % (ulib.tools.coding.utf8(data[:20]))
		self.assertFetcher(tfile.isValidTorrentData(data), message)


	### Private ###

	def __customAssert(self, exception, arg, message = "") :
		if not arg :
			raise exception(message)

