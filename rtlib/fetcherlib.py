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
import time


##### Exceptions #####
class CommonFetcherError(Exception) :
	pass

class LoginError(CommonFetcherError) :
	pass

class FetcherError(CommonFetcherError) :
	pass


##### Public classes #####
class AbstractFetcher(object) :
	def __init__(self, user_name, passwd, interactive_flag = False) :
		object.__init__(self)


	### Public ###

	@classmethod
	def name(self) :
		raise NotImplementedError

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

