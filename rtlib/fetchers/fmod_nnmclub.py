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
from .. import tfile


##### Public constants #####
FETCHER_NAME = "nnm-club"
FETCHER_VERSION = 1

NNMCLUB_DOMAIN = "nnm-club.me"
NNMCLUB_URL = "http://%s" % (NNMCLUB_DOMAIN)
NNMCLUB_LOGIN_URL = "%s/forum/login.php" % (NNMCLUB_URL)
NNMCLUB_DL_URL = "%s/forum/download.php" % (NNMCLUB_URL)
NNMCLUB_SCRAPE_URL = "http://bt.%s:2710/scrape" % (NNMCLUB_DOMAIN)

NNMCLUB_ENCODING = "cp1251"
NNMCLUB_FINGERPRINT = b"<link rel=\"canonical\" href=\"http://nnm-club.me/\">"
REPLACE_DOMAINS = ("nnm-club.ru", "nnm-club.me")


##### Public classes #####
class Fetcher(fetcherlib.AbstractFetcher) :
    def __init__(self, *args_tuple, **kwargs_dict) :
        self._comment_regexp = re.compile(r"http://nnm-club\.(me|ru)/forum/viewtopic\.php\?p=(\d+)")
        self._torrent_id_regexp = re.compile(r"filelst.php\?attach_id=([a-zA-Z0-9]+)")

        self._cookie_jar = None
        self._opener = None

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
        return ( not self._comment_regexp.match(torrent.comment() or "") is None )

    def ping(self) :
        opener = fetcherlib.buildTypicalOpener(proxy_url=self.proxyUrl())
        data = self._readUrlRetry(NNMCLUB_URL, opener=opener)
        self.assertSite(NNMCLUB_FINGERPRINT in data)

    def login(self) :
        self.assertNonAnonymous()
        self._cookie_jar = http.cookiejar.CookieJar()
        self._opener = fetcherlib.buildTypicalOpener(self._cookie_jar, self.proxyUrl())
        try :
            self._tryLogin()
        except :
            self._cookie_jar = None
            self._opener = None
            raise

    def loggedIn(self) :
        return ( not self._opener is None )

    def torrentChanged(self, torrent) :
        self.assertMatch(torrent)
        client_agent = self.clientAgent()
        headers_dict = ( { "User-Agent" : client_agent } if not client_agent is None else None )
        data = self._readUrlRetry(NNMCLUB_SCRAPE_URL+("?info_hash=%s" % (torrent.scrapeHash())), headers_dict=headers_dict)
        return ( not "files" in tfile.decodeData(data) )

    def fetchTorrent(self, torrent) :
        self.assertMatch(torrent)
        data = self._readUrlRetry(torrent.comment().replace(*REPLACE_DOMAINS)).decode(NNMCLUB_ENCODING)

        torrent_id_match = self._torrent_id_regexp.search(data)
        self.assertFetcher(not torrent_id_match is None, "Unknown torrent_id")
        torrent_id = torrent_id_match.group(1)

        data = self._readUrlRetry(NNMCLUB_DL_URL+("?id=%s" % (torrent_id)))
        self.assertValidTorrentData(data)
        return data


    ### Private ###

    def _tryLogin(self) :
        post_dict = {
            "username" : self.userName(),
            "password" : self.passwd(),
            "redirect" : "",
            "login"    : "\xc2\xf5\xee\xe4",
        }
        post_data = urllib.parse.urlencode(post_dict).encode(NNMCLUB_ENCODING)
        data = self._readUrlRetry(NNMCLUB_LOGIN_URL, post_data).decode(NNMCLUB_ENCODING)
        self.assertLogin("[ %s ]" % (self.userName()) in data, "Invalid login")

    def _readUrlRetry(self, url, data = None, headers_dict = None, opener = None) :
        opener = ( opener or self._opener )
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
        )

