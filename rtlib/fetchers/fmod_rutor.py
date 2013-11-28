#####
#
#    rtfetch -- Plugin for rutor (http://rutor.org)
#    Copyright (C) 2013  Devaev Maxim <mdevaev@gmail.com>
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


import re

from .. import fetcherlib


##### Public constants #####
FETCHER_NAME = "rutor"
FETCHER_VERSION = 0

RUTOR_DOMAIN = "rutor.org"
RUTOR_URL = "http://%s" % (RUTOR_DOMAIN)
RUTOR_DL_URL = "http://d.%s/download" % (RUTOR_DOMAIN)

RUTOR_ENCODING = "utf-8"
RUTOR_FINGERPRINT = b"<link rel=\"shortcut icon\" href=\"http://s.rutor.org/favicon.ico\" />"


##### Public classes #####
class Fetcher(fetcherlib.AbstractFetcher) :
    def __init__(self, *args_tuple, **kwargs_dict) :
        self.__comment_regexp = re.compile(r"^http://rutor\.org/torrent/(\d+)$")
        self.__hash_regexp = re.compile(r"<div id=\"download\">\s+<a href=\"magnet:\?xt=urn:btih:([a-fA-F0-9]{40})")

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
        data = self.__readUrlRetry(RUTOR_URL, opener=opener)
        self.assertSite(RUTOR_FINGERPRINT in data)

    def login(self) :
        self.__opener = fetcherlib.buildTypicalOpener(proxy_url=self.proxyUrl())

    def loggedIn(self) :
        return ( not self.__opener is None )

    def torrentChanged(self, torrent) :
        self.assertMatch(torrent)
        return ( torrent.hash() != self.__fetchHash(torrent) )

    def fetchTorrent(self, torrent) :
        comment_match = self.__comment_regexp.match(torrent.comment() or "")
        self.assertFetcher(not comment_match is None, "No comment match")
        topic_id = comment_match.group(1)
        data = self.__readUrlRetry("%s/%s" % (RUTOR_DL_URL, topic_id))
        self.assertValidTorrentData(data)
        return data


    ### Private ###

    def __fetchHash(self, torrent) :
        data = self.__readUrlRetry(torrent.comment()).decode(RUTOR_ENCODING)
        hash_match = self.__hash_regexp.search(data)
        self.assertFetcher(not hash_match is None, "Hash not found")
        return hash_match.group(1).lower()

    def __readUrlRetry(self, url, opener = None) :
        opener = ( opener or self.__opener )
        assert not opener is None

        user_agent = self.userAgent()
        headers_dict = ( { "User-Agent" : user_agent } if not user_agent is None else None )

        return fetcherlib.readUrlRetry(opener, url,
            headers_dict=headers_dict,
            timeout=self.timeout(),
            retries=self.urlRetries(),
            sleep_time=self.urlSleepTime(),
        )

