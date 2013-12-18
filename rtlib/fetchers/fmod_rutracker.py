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
RUTRACKER_FINGERPRINT = b"<link rel=\"shortcut icon\" href=\"http://static.rutracker.org/favicon.ico\" type=\"image/x-icon\">"


##### Public classes #####
class Fetcher(fetcherlib.AbstractFetcher) :
    def __init__(self, *args_tuple, **kwargs_dict) :
        self._comment_regexp = re.compile(r"http://rutracker\.org/forum/viewtopic\.php\?t=(\d+)")

        self._cap_static_regexp = re.compile(r"\"(http://static\.rutracker\.org/captcha/[^\"]+)\"")
        self._cap_sid_regexp = re.compile(r"name=\"cap_sid\" value=\"([a-zA-Z0-9]+)\"")
        self._cap_code_regexp = re.compile(r"name=\"(cap_code_[a-zA-Z0-9]+)\"")

        self._hash_regexp = re.compile(r"<span id=\"tor-hash\">([a-zA-Z0-9]+)</span>")

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
        return ( self._comment_regexp.match(torrent.comment() or "") is not None )

    def ping(self) :
        opener = fetcherlib.buildTypicalOpener(proxy_url=self.proxyUrl())
        data = self._readUrlRetry(RUTRACKER_URL, opener=opener)
        self.assertSite(RUTRACKER_FINGERPRINT in data)

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
        return ( torrent.hash() != self._fetchHash(torrent) )

    def fetchTorrent(self, torrent) :
        comment_match = self._comment_regexp.match(torrent.comment() or "")
        self.assertFetcher(comment_match is not None, "No comment match")
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
        self._cookie_jar.set_cookie(cookie)

        data = self._readUrlRetry(RUTRACKER_DL_URL+("?t=%s" % (topic_id)), b"", {
                "Referer"    : RUTRACKER_VIEWTOPIC_URL+("?t=%s" % (topic_id)),
                "Origin"     : "http://%s" % (RUTRACKER_DOMAIN),
            })
        self.assertValidTorrentData(data)
        return data


    ### Private ###

    def _tryLogin(self) :
        post_dict = {
            "login_username" : self.userName().encode(RUTRACKER_ENCODING),
            "login_password" : self.passwd().encode(RUTRACKER_ENCODING),
            "login"          : b"\xc2\xf5\xee\xe4",
        }
        post_data = urllib.parse.urlencode(post_dict).encode(RUTRACKER_ENCODING)
        data = self._readUrlRetry(RUTRACKER_LOGIN_URL, post_data).decode(RUTRACKER_ENCODING)

        cap_static_match = self._cap_static_regexp.search(data)
        if cap_static_match is not None :
            self.assertLogin(self.isInteractive(), "Required captcha")

            cap_sid_match = self._cap_sid_regexp.search(data)
            cap_code_match = self._cap_code_regexp.search(data)
            self.assertLogin(cap_sid_match is not None, "Unknown cap_sid")
            self.assertLogin(cap_code_match is not None, "Unknown cap_code")

            post_dict[cap_code_match.group(1)] = self.decodeCaptcha(cap_static_match.group(1))
            post_dict["cap_sid"] = cap_sid_match.group(1)
            post_data = urllib.parse.urlencode(post_dict).encode(RUTRACKER_ENCODING)
            data = self._readUrlRetry(RUTRACKER_LOGIN_URL, post_data).decode(RUTRACKER_ENCODING)
            self.assertLogin(self._cap_static_regexp.search(data) is None, "Invalid captcha or password")

    def _fetchHash(self, torrent) :
        data = self._readUrlRetry(torrent.comment()).decode(RUTRACKER_ENCODING)
        hash_match = self._hash_regexp.search(data)
        self.assertFetcher(hash_match is not None, "Hash not found")
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
            retry_codes_list=(503, 404),
        )

