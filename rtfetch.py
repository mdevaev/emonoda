#!/usr/bin/env python2
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


import sys
import os
import urllib
import urllib2
import xmlrpclib
import cookielib
import operator
import bencode
import hashlib
import argparse
import ConfigParser
import shutil
import json
import time
import re


##### Public constants #####
BROWSER_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1"
CLIENT_USER_AGENT = "rtorrent/0.9.2/0.13.2"

NNMCLUB_DOMAIN = "nnm-club.ru"
NNMCLUB_LOGIN_URL = "http://%s/forum/login.php" % (NNMCLUB_DOMAIN)
#NNMCLUB_VIEWTOPIC_URL = "http://%s/forum/viewtopic.php" % (NNMCLUB_DOMAIN)
NNMCLUB_DL_URL = "http://%s/forum/download.php" % (NNMCLUB_DOMAIN)
NNMCLUB_SCRAPE_URL = "http://%s:2710/scrape" % (NNMCLUB_DOMAIN)

RUTRACKER_DOMAIN = "rutracker.org"
RUTRACKER_LOGIN_URL = "http://login.%s/forum/login.php" % (RUTRACKER_DOMAIN)
RUTRACKER_VIEWTOPIC_URL = "http://%s/forum/viewtopic.php" % (RUTRACKER_DOMAIN)
RUTRACKER_DL_URL = "http://dl.%s/forum/dl.php" % (RUTRACKER_DOMAIN)
RUTRACKER_AJAX_URL = "http://%s/forum/ajax.php" % (RUTRACKER_DOMAIN)


##### Public classes #####
class Fetcher(object) :
	def __init__(self, user_name, passwd, interactive_flag = False) :
		object.__init__(self)

	@classmethod
	def name(self) :
		raise NotImplementedError

	def match(self, bencode_dict) :
		raise NotImplementedError

	def login(self) :
		raise NotImplementedError

	def loggedIn(self) :
		raise NotImplementedError

	def torrentChanged(self, bencode_dict) :
		raise NotImplementedError

	def fetchTorrent(self, bencode_dict) :
		raise NotImplementedError


###
class NnmClubFetcher(Fetcher) :
	def __init__(self, user_name, passwd, interactive_flag = False) :
		Fetcher.__init__(self, user_name, passwd, interactive_flag)

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
		torrent_hash = torrentHash(bencode_dict)
		scrape_hash = ""
		for index in xrange(0, len(torrent_hash), 2) :
			scrape_hash += "%{0}".format(torrent_hash[index:index + 2])
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


class RuTrackerFetcher(Fetcher) :
	def __init__(self, user_name, passwd, interactive_flag = False) :
		Fetcher.__init__(self, user_name, passwd, interactive_flag)

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

	def match(self, bencode_dict) :
		return ( not self.__comment_regexp.match(bencode_dict["comment"]) is None )

	def login(self) :
		self.__cookie_jar = cookielib.CookieJar()
		self.__opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.__cookie_jar))

		post_dict = {
			"login_username" : self.__user_name,
			"login_password" : self.__passwd,
			"login" : "%C2%F5%EE%E4",
		}
		web_file = self.__opener.open(RUTRACKER_LOGIN_URL, urllib.urlencode(post_dict))
		data = web_file.read()

		cap_static_match = self.__cap_static_regexp.search(data)
		if not cap_static_match is None :
			if not self.__interactive_flag :
				raise RuntimeError("Required captcha")
			else :
				cap_sid_match = self.__cap_sid_regexp.search(data)
				cap_code_match = self.__cap_code_regexp.search(data)
				assert not cap_sid_match is None
				assert not cap_code_match is None

				print ":: Enter the capthca [ %s ]: " % (cap_static_match.group(1)),
				post_dict[cap_code_match.group(1)] = raw_input()
				post_dict["cap_sid"] = cap_sid_match.group(1)
				web_file = self.__opener.open(RUTRACKER_LOGIN_URL, urllib.urlencode(post_dict))
				if not self.__cap_static_regexp.search(web_file.read()) is None :
					raise RuntimeError("Invalid captcha")

	def loggedIn(self) :
		return ( not self.__opener is None )

	def torrentChanged(self, bencode_dict) :
		old_hash = torrentHash(bencode_dict)
		new_hash = self.fetchHash(bencode_dict)
		return ( old_hash != new_hash )

	def fetchTorrent(self, bencode_dict) :
		comment_match = self.__comment_regexp.match(bencode_dict["comment"])
		assert not comment_match is None, "No comment"
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
				"User-Agent" : BROWSER_USER_AGENT,
			})

		data = self.readUrlRetry(request)
		bencode.bdecode(data)
		return data


	### Private ###

	def fetchHash(self, bencode_dict) :
		comment_match = self.__comment_regexp.match(bencode_dict["comment"])
		assert not comment_match is None, "No comment"

		data = self.readUrlRetry(bencode_dict["comment"])
		hash_t_match = self.__hash_t_regexp.search(data)
		hash_form_token_match = self.__hash_form_token_regexp.search(data)
		assert not hash_t_match is None, "Unknown t_hash"
		assert not hash_form_token_match is None, "Unknown form_token"

		post_dict = {
			"action" : "get_info_hash",
			"topic_id" : comment_match.group(1),
			"t_hash" : hash_t_match.group(1),
			"form_token" : hash_form_token_match.group(1),
		}
		request = urllib2.Request(RUTRACKER_AJAX_URL, urllib.urlencode(post_dict), headers={
				"User-Agent" : BROWSER_USER_AGENT
			})
		response_dict = json.loads(self.readUrlRetry(request))
		if response_dict.has_key("ih_hex") :
			return response_dict["ih_hex"].upper()
		elif response_dict.has_key("error_msg") :
			raise RuntimeError(unicode(response_dict["error_msg"]).encode("utf-8"))
		else :
			raise RuntimeError("Invalid response: %s" % (str(response_dict)))

	def readUrlRetry(self, *args_list, **kwargs_dict) :
		count = 0
		while True :
			try :
				return self.__opener.open(*args_list, **kwargs_dict).read()
			except urllib2.HTTPError, err :
				if count >= 10 or not err.code in (503, 404) :
					raise
				count += 1
				time.sleep(1)


class RTorrent(object) :
	# XXX: API description: http://code.google.com/p/gi-torrent/wiki/rTorrent_XMLRPC_reference

	def __init__(self, url) :
		self.__server = xmlrpclib.ServerProxy(url)

	def removeTorrent(self, torrent_hash) :
		self.__server.d.erase(torrent_hash)

	def loadTorrent(self, torrent_file_path) :
		self.__server.load_start(torrent_file_path)


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

def update(fetchers_list, interface, src_dir_path, backup_dir_path) :
	print

	unknown_count = 0
	passed_count = 0
	updated_count = 0
	error_count = 0

	for (torrent_file_name, bencode_dict) in sorted(torrents(src_dir_path).items(), key=operator.itemgetter(0)) :
		comment = bencode_dict["comment"]

		unknown_flag = True
		for fetcher in fetchers_list :
			if not fetcher.match(bencode_dict) :
				continue
			unknown_flag = False

			try :
				if not fetcher.loggedIn() :
					fetcher.login()

				if not fetcher.torrentChanged(bencode_dict) :
					print "[ ] %s %s" % (fetcher.name(), torrent_file_name)
					passed_count += 1
					continue

				torrent_data = fetcher.fetchTorrent(bencode_dict)

				torrent_file_path = os.path.join(src_dir_path, torrent_file_name)
				if not backup_dir_path is None :
					shutil.copyfile(torrent_file_path, os.path.join(backup_dir_path, "%s.%d.bak" % (torrent_file_name, time.time())))
				if not interface is None :
					interface.removeTorrent(torrentHash(bencode_dict))

				with open(torrent_file_path, "w") as torrent_file :
					torrent_file.write(torrent_data)
				if not interface is None :
					interface.loadTorrent(torrent_file_path)

				print "[+] %s %s --- %s" % (fetcher.name(), torrent_file_name, comment)
				updated_count += 1
			except Exception, err :
				print "[-] %s %s --- %s :: %s(%s)" % (fetcher.name(), torrent_file_name, comment, type(err).__name__, str(err))
				error_count += 1

			break

		if unknown_flag :
			print "[!] UNKNOWN %s --- %s" % (torrent_file_name, comment)
			unknown_count += 1

	print
	print "-"*10
	print "Unknown: %d" % (unknown_count)
	print "Passed: %d" % (passed_count)
	print "Updated: %d" % (updated_count)
	print "Errors: %d" % (error_count)
	print


##### Main #####
def main() :
	cli_parser = argparse.ArgumentParser(description="Update rtorrent files from popular trackers")
	cli_parser.add_argument("-c", "--config", dest="config_file_path", action="store", required=True)
	cli_parser.add_argument("-i", "--interative", dest="interactive_flag", action="store_true", default=False)
	cli_parser.add_argument("-s", "--source-dir", dest="src_dir_path", action="store", default=".")
	cli_parser.add_argument("-b", "--backup-dir", dest="backup_dir_path", action="store", default=None)
	cli_parser.add_argument("--no-rtorrent", dest="no_rtorrent_flag", action="store_true", default=False)
	cli_parser.add_argument("--xmlrpc-url", dest="xmlrpc_url", action="store", default="http://localhost/RPC2")
	cli_options = cli_parser.parse_args(sys.argv[1:])

	fetchers_list = []
	config_parser = ConfigParser.ConfigParser()
	config_parser.read(cli_options.config_file_path)
	for fetcher_class in (NnmClubFetcher, RuTrackerFetcher) :
		fetcher_name = fetcher_class.name()
		if config_parser.has_section(fetcher_name) :
			fetchers_list.append(fetcher_class(
					config_parser.get(fetcher_name, "login"),
					config_parser.get(fetcher_name, "passwd"),
					cli_options.interactive_flag,
				))

	if len(fetchers_list) == 0 :
		print >> sys.stderr, "No available fetchers in config"
		sys.exit(1)

	rtorrent = ( RTorrent(cli_options.xmlrpc_url) if not cli_options.no_rtorrent_flag else None )
	update(fetchers_list, rtorrent, cli_options.src_dir_path, cli_options.backup_dir_path)


###
if __name__ == "__main__" :
	main()

