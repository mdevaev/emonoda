#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
#
#    rtfetch -- Update rtorrent files from <http://rutracker.org>
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
import getpass
import argparse
import shutil
import json
import time
import re


##### Public constants #####
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1"

RUTRACKER_DOMAIN = "rutracker.org"
RUTRACKER_LOGIN_URL = "http://login.%s/forum/login.php" % (RUTRACKER_DOMAIN)
RUTRACKER_VIEWTOPIC_URL = "http://%s/forum/viewtopic.php" % (RUTRACKER_DOMAIN)
RUTRACKER_DL_URL = "http://dl.%s/forum/dl.php" % (RUTRACKER_DOMAIN)
RUTRACKER_AJAX_URL = "http://%s/forum/ajax.php" % (RUTRACKER_DOMAIN)


##### Public classes #####
class RuTracker(object) :
	def __init__(self, user_name, passwd, interactive_flag = False) :
		object.__init__(self)

		self.__user_name = user_name
		self.__passwd = passwd
		self.__interactive_flag = interactive_flag

		self.__comment_regexp = re.compile(r"http://rutracker\.org/forum/viewtopic\.php\?t=(\d+)")

		self.__cap_static_regexp = re.compile(r"\"(http://static\.rutracker\.org/captcha/[^\"]+)\"")
		self.__cap_sid_regexp = re.compile(r"name=\"cap_sid\" value=\"([a-zA-Z0-9]+)\"")
		self.__cap_code_regexp = re.compile(r"name=\"(cap_code_[a-zA-Z0-9]+)\"")

		self.__hash_t_regexp = re.compile(r"t_hash\s*:\s*'([a-zA-Z0-9]+)'")
		self.__hash_form_token_regexp = re.compile(r"name=\"form_token\" value=\"([a-zA-Z0-9]+)\"")


	### Public ###

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
			"login" : "%C2%F5%EE%E4"
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
				if self.__cap_static_regexp.search(web_file.read()) is None :
					raise RuntimeError("Invalid captcha")

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
			"form_token" : hash_form_token_match.group(1)
		}
		request = urllib2.Request(RUTRACKER_AJAX_URL, urllib.urlencode(post_dict), headers={
				"User-Agent" : USER_AGENT
			})
		response_dict = json.loads(self.readUrlRetry(request))
		if response_dict.has_key("ih_hex") :
			return response_dict["ih_hex"].upper()
		elif response_dict.has_key("error_msg") :
			raise RuntimeError(unicode(response_dict["error_msg"]).encode("utf-8"))
		else :
			raise RuntimeError("Invalid response: %s" % (str(response_dict)))

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
			rfc2109=False
		)
		self.__cookie_jar.set_cookie(cookie)
		request = urllib2.Request(RUTRACKER_DL_URL+("?t=%s" % (topic_id)), "", headers={
				"Referer" : RUTRACKER_VIEWTOPIC_URL+("?t=%s" % (topic_id)),
				"Origin" : "http://%s" % (RUTRACKER_DOMAIN),
				"User-Agent" : USER_AGENT
			})

		data = self.readUrlRetry(request)
		bencode.bdecode(data)
		return data


	### Private ###

	def readUrlRetry(self, *args_list, **kwargs_dict) :
		count = 0
		while True :
			try :
				return self.__opener.open(*args_list, **kwargs_dict).read()
			except urllib2.HTTPError, err :
				if count >= 10 or not err.code in [503, 404] :
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
			torrent_hash = hashlib.sha1(bencode.bencode(bencode_dict["info"])).hexdigest().upper()
			torrents_dict[torrent_file_name] = {
				"bencode" : bencode_dict,
				"hash" : torrent_hash
			}
	return torrents_dict

def update(fetcher, interface, src_dir_path, backup_dir_path) :
	print

	unknown_count = 0
	passed_count = 0
	updated_count = 0
	error_count = 0

	for (torrent_file_name, torrent_dict) in sorted(torrents(src_dir_path).items(), key=operator.itemgetter(0)) :
		bencode_dict = torrent_dict["bencode"]
		comment = bencode_dict["comment"]

		if not fetcher.match(bencode_dict) :
			print "[!] UNKNOWN %s --- %s" % (torrent_file_name, comment)
			unknown_count += 1
			continue

		try :
			if torrent_dict["hash"] == fetcher.fetchHash(bencode_dict) :
				print "[ ] %s %s" % (fetcher.name(), torrent_file_name)
				passed_count += 1
				continue

			torrent_data = fetcher.fetchTorrent(bencode_dict)

			torrent_file_path = os.path.join(src_dir_path, torrent_file_name)
			if not backup_dir_path is None :
				shutil.copyfile(torrent_file_path, os.path.join(backup_dir_path, "%s.%d.bak" % (torrent_file_name, time.time())))
			if not interface is None :
				interface.removeTorrent(torrent_dict["hash"])

			with open(torrent_file_path, "w") as torrent_file :
				torrent_file.write(torrent_data)
			if not interface is None :
				interface.loadTorrent(torrent_file_path)

			print "[+] %s %s --- %s" % (fetcher.name(), torrent_file_name, comment)
			updated_count += 1
		except Exception, err :
			print "[-] %s %s --- %s :: %s(%s)" % (fetcher.name(), torrent_file_name, comment, type(err).__name__, str(err))
			error_count += 1

	print
	print "-"*10
	print "Unknown: %d" % (unknown_count)
	print "Passed: %d" % (passed_count)
	print "Updated: %d" % (updated_count)
	print "Errors: %d" % (error_count)
	print


##### Main #####
def main() :
	parser = argparse.ArgumentParser(description="Update rtorrent files from http://rutracker.org")
	parser.add_argument("-u", "--user", dest="user_name", action="store", required=True)
	parser.add_argument("-p", "--passwd", dest="passwd", action="store", default=None)
	parser.add_argument("-i", "--interative", dest="interactive_flag", action="store_true", default=False)
	parser.add_argument("-s", "--source-dir", dest="src_dir_path", action="store", default=".")
	parser.add_argument("-b", "--backup-dir", dest="backup_dir_path", action="store", default=None)
	parser.add_argument("--no-rtorrent", dest="no_rtorrent_flag", action="store_true", default=False)
	parser.add_argument("--xmlrpc-url", dest="xmlrpc_url", action="store", default="http://localhost/RPC2")
	options = parser.parse_args(sys.argv[1:])

	if options.passwd is None :
		options.passwd = getpass.getpass(":: RuTracker password for user \"%s\": " % (options.user_name))

	rutracker = RuTracker(options.user_name, options.passwd, options.interactive_flag)
	rutracker.login()
	rtorrent = ( RTorrent(options.xmlrpc_url) if not options.no_rtorrent_flag else None )

	update(rutracker, rtorrent, options.src_dir_path, options.backup_dir_path)


if __name__ == "__main__" :
	main()

