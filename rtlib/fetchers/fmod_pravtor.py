#####
#
#    rtfetch -- Plugin for http://pravtor.ru (based on rutracker.py)
#    Copyright (C) 2012  Devaev Maxim <mdevaev@gmail.com>
#    Copyright (C) 2013  Vitaly Lipatov <lav@etersoft.ru>
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
FETCHER_NAME = "pravtor"
FETCHER_VERSION = 0

PRAVTOR_DOMAIN = "pravtor.ru"
PRAVTOR_URL = "http://%s" % (PRAVTOR_DOMAIN)
PRAVTOR_LOGIN_URL = "%s/login.php" % (PRAVTOR_URL)
PRAVTOR_VIEWTOPIC_URL = "%s/viewtopic.php" % (PRAVTOR_URL)
PRAVTOR_DL_URL = "%s/download.php" % (PRAVTOR_URL)

PRAVTOR_ENCODING = "cp1251"
PRAVTOR_FINGERPRINT = b"<img src=\"/images/pravtor_beta1.png\""


##### Public classes #####
class Fetcher(fetcherlib.AbstractFetcher) :
    def __init__(self, *args_tuple, **kwargs_dict) :
        self._comment_regexp = re.compile(r"http://pravtor\.(ru|spb\.ru)/viewtopic\.php\?p=(\d+)")

        self._hash_regexp = re.compile(r"<span id=\"tor-hash\">([a-fA-F0-9]+)</span>")
        self._loginform_regexp = re.compile(r"<!--login form-->")
        self._torrent_id_regexp = re.compile(r"<a href=\"download.php\?id=(\d+)\" class=\"(leech|seed|gen)med\">")

        self._cookie_jar = None
        self._opener = None
        self._torrent_id = None

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
        return ( self._comment_regexp.match(torrent.comment() or "") is not None )

    def ping(self) :
        opener = fetcherlib.buildTypicalOpener(proxy_url=self.proxyUrl())
        data = self._readUrlRetry(PRAVTOR_URL, opener=opener)
        self.assertSite(PRAVTOR_FINGERPRINT in data)

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
        return ( self._opener is not None )

    def torrentChanged(self, torrent) :
        self.assertMatch(torrent)
        self._torrent_id = None
        return ( torrent.hash() != self._fetchHash(torrent) )

    def fetchTorrent(self, torrent) :
        comment_match = self._comment_regexp.match(torrent.comment() or "")
        self.assertFetcher(comment_match is not None, "No comment match")
        topic_id = comment_match.group(1)

        assert self._torrent_id is not None, "Programming error, torrent_id == None"

        cookie = http.cookiejar.Cookie(
            version=0,
            name="bb_dl",
            value=topic_id,
            port=None,
            port_specified=False,
            domain="",
            domain_specified=False,
            domain_initial_dot=False,
            path="/",
            path_specified=True,
            secure=False,
            expires=None,
            discard=True,
            comment=None,
            comment_url=None,
            rest={ "HttpOnly" : None },
            rfc2109=False,
        )
        self._cookie_jar.set_cookie(cookie)

        data = self._readUrlRetry(PRAVTOR_DL_URL+("?id=%d" % (self._torrent_id)), b"", {
                "Referer" : PRAVTOR_VIEWTOPIC_URL+("?t=%s" % (topic_id)),
                "Origin"  : "http://%s" % (PRAVTOR_DOMAIN),
            })
        self.assertValidTorrentData(data)
        return data


    ### Private ###

    def _tryLogin(self) :
        post_dict = {
            "login_username" : self.userName().decode(PRAVTOR_ENCODING),
            "login_password" : self.passwd().decode(PRAVTOR_ENCODING),
            "login"          : b"\xc2\xf5\xee\xe4",
        }
        post_data = urllib.parse.urlencode(post_dict).encode(PRAVTOR_ENCODING)
        data = self._readUrlRetry(PRAVTOR_LOGIN_URL, post_data).decode(PRAVTOR_ENCODING)
        self.assertLogin(self._loginform_regexp.search(data) is None, "Invalid login or password")

    def _fetchHash(self, torrent) :
        data = self._readUrlRetry(torrent.comment()).decode(PRAVTOR_ENCODING)

        hash_match = self._hash_regexp.search(data)
        self.assertFetcher(hash_match is not None, "Hash is not found")

        torrent_id = self._torrent_id_regexp.search(data)
        self.assertFetcher(torrent_id is not None, "Torrent ID is not found")
        self._torrent_id = int(torrent_id.group(1))

        return hash_match.group(1).lower()

    def _readUrlRetry(self, url, data = None, headers_dict = None, opener = None) :
        opener = ( opener or self._opener )
        assert opener is not None

        headers_dict = ( headers_dict or {} )
        user_agent = self.userAgent()
        if user_agent is not None :
            headers_dict.setdefault("User-Agent", user_agent)

        return fetcherlib.readUrlRetry(opener, url, data,
            headers_dict=headers_dict,
            timeout=self.timeout(),
            retries=self.urlRetries(),
            sleep_time=self.urlSleepTime(),
        )

