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


import socket
import urllib2
import json
import time


#####
UPSTREAM_URL = "https://raw.github.com/mdevaev/rtfetch/master"
VERSIONS_URL = UPSTREAM_URL + "/fetchers.json"


##### Exceptions #####
class CommonFetcherError(Exception) :
	pass

class LoginError(CommonFetcherError) :
	pass

class FetcherError(CommonFetcherError) :
	pass


##### Public methods #####
def readUrlRetry(*args_list, **kwargs_dict) :
	opener = kwargs_dict.pop("opener", None)
	if opener is None :
		opener = urllib2.build_opener()
	retries = kwargs_dict.pop("retries", 10)
	sleep_time = kwargs_dict.pop("sleep_time", 1)
	retry_codes_list = kwargs_dict.pop("retry_codes_list", (503, 502, 500))
	retry_timeout_flag = kwargs_dict.pop("retry_timeout_flag", True)

	while True :
		try :
			return opener.open(*args_list, **kwargs_dict).read()
		except (socket.timeout, urllib2.HTTPError), err :
			if retries == 0 :
				raise
			if isinstance(err, socket.timeout) :
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
		upstream_version = versions_dict[plugin_name]["version"]
		if local_version < upstream_version :
			print "# Plug-in \"%s\" is outdated." % (plugin_name)
			print "#    Local version:    %d" % (local_version)
			print "#    Upstream version: %d" % (upstream_version)
			print "# The plugin can not work properly. It is recommended to upgrade the program."
			print
			ok_flag = False
	return ok_flag


##### Public classes #####
class AbstractFetcher(object) :
	def __init__(self, user_name, passwd, interactive_flag = False) :
		object.__init__(self)


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
		self.customAssert(LoginError, *args_list)

	def assertFetcher(self, *args_list) :
		self.customAssert(FetcherError, *args_list)


	### Private ###

	def customAssert(self, exception, arg, message = "") :
		if not arg :
			raise exception(message)

