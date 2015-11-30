"""
    Emonoda -- A set of tools to organize and manage your torrents
    Copyright (C) 2015  Devaev Maxim <mdevaev@gmail.com>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


import socket
import urllib.parse
import urllib.error
import http.client
import http.cookiejar
import json

import pytz

from ...optconf import Option
from ...optconf import SecretOption
from ...optconf.converters import as_string_or_none

from ... import tfile
from ... import web

from .. import BasePlugin
from .. import BaseExtension


# =====
class FetcherError(Exception):
    pass


class AuthError(FetcherError):
    pass


class LogicError(FetcherError):
    pass


class NetworkError(FetcherError):
    def __init__(self, sub):
        super().__init__()
        self._sub = sub

    def __str__(self):
        return "{}: {}".format(type(self._sub).__name__, str(self._sub))


# =====
def _assert(exception, arg, msg=""):
    if not arg:
        raise exception(msg)


class BaseFetcher(BasePlugin):  # pylint: disable=too-many-instance-attributes
    def __init__(self, timeout, retries, retries_sleep, user_agent, proxy_url,
                 check_version, check_fingerprint, **_):

        self._timeout = timeout
        self._retries = retries
        self._retries_sleep = retries_sleep
        self._user_agent = user_agent
        self._proxy_url = proxy_url
        self._check_version = check_version
        self._check_fingerprint = check_fingerprint

        self._comment_regexp = None
        self._retry_codes = (500, 502, 503)
        self._cookie_jar = None
        self._opener = None

    @classmethod
    def get_version(cls):
        raise NotImplementedError

    @classmethod
    def get_fingerprint(cls):
        raise NotImplementedError

    @classmethod
    def get_options(cls):
        return {
            "timeout":           Option(default=10.0, type=float, help="Timeout for HTTP client"),
            "retries":           Option(default=20, help="The number of retries to handle tracker-specific HTTP errors"),
            "retries_sleep":     Option(default=1.0, help="Sleep interval between failed retries"),
            "user_agent":        Option(default="Mozilla/5.0", help="User-Agent for site"),
            "proxy_url":         Option(default=None, type=as_string_or_none, help="URL of HTTP/SOCKS4/SOCKS5 proxy"),
            "check_fingerprint": Option(default=True, help="Check the site fingerprint"),
            "check_version":     Option(default=True, help="Check the fetcher version from GitHub"),
        }

    def is_torrent_changed(self, torrent):
        raise NotImplementedError

    def fetch_new_data(self, torrent):
        raise NotImplementedError

    # ===

    def _init_opener(self, with_cookies):
        if with_cookies:
            self._cookie_jar = http.cookiejar.CookieJar()
            self._opener = web.build_opener(self._proxy_url, self._cookie_jar)
        else:
            self._opener = web.build_opener(self._proxy_url)

    def _build_opener(self):
        return web.build_opener(self._proxy_url)

    def _read_url(self, *args, **kwargs):
        try:
            return self._read_url_nofe(*args, **kwargs)
        except (
            socket.timeout,
            urllib.error.HTTPError,
            urllib.error.URLError,
            http.client.IncompleteRead,
            http.client.BadStatusLine,
            ConnectionResetError,
        ) as err:
            raise NetworkError(err)

    def _read_url_nofe(self, url, data=None, headers=None, opener=None):
        opener = (opener or self._opener)
        assert opener is not None

        headers = (headers or {})
        headers.setdefault("User-Agent", self._user_agent)

        return web.read_url(
            opener=opener,
            url=url,
            data=data,
            headers=headers,
            timeout=self._timeout,
            retries=self._retries,
            retries_sleep=self._retries_sleep,
            retry_codes=self._retry_codes,
        )

    # ===

    def is_matched_for(self, torrent):
        assert self._comment_regexp is not None
        return (self._comment_regexp.match(torrent.get_comment() or "") is not None)

    def _assert_logic(self, arg, *args):
        _assert(LogicError, arg, *args)

    def _assert_match(self, torrent):
        self._assert_logic(self.is_matched_for(torrent), "No match with torrent")

    def _assert_valid_data(self, data):
        msg = "Received an invalid torrent data: {} ...".format(repr(data[:20]))
        self._assert_logic(tfile.is_valid_data(data), msg)

    # ===

    def test(self):
        if self._check_fingerprint or self._check_version:
            opener = web.build_opener(self._proxy_url)
            info = self._get_upstream_info(opener)
        if self._check_fingerprint:
            self._test_fingerprint(info["fingerprint"], opener)
        if self._check_version:
            self._test_version(info["version"])

    def _get_upstream_info(self, opener):
        try:
            return json.loads(self._read_url_nofe(
                url="https://raw.githubusercontent.com/mdevaev/emonoda/master/fetchers/{}.json".format(self.get_name()),
                opener=opener,
            ).decode("utf-8"))
        except urllib.error.HTTPError as err:
            if err.code == 404:
                return self._get_local_info()
            raise

    @classmethod
    def _get_local_info(cls):
        return {
            "fingerprint": cls.get_fingerprint(),
            "version":     cls.get_version(),
        }

    def _test_fingerprint(self, fingerprint, opener):
        data = self._read_url(fingerprint["url"], opener=opener)
        msg = "Invalid site body, maybe tracker is blocked"
        try:
            page = data.decode(fingerprint["encoding"])
        except UnicodeDecodeError:
            raise FetcherError(msg)
        _assert(FetcherError, fingerprint["text"] in page, msg)

    def _test_version(self, upstream):
        local = self.get_version()
        _assert(FetcherError, local >= upstream, "Fetcher is outdated (ver. local:{}, upstream:{})."
                                                 " I recommend to update the program".format(local, upstream))


class WithLogin(BaseExtension):
    def __init__(self, user, passwd, **_):
        self._user = user
        self._passwd = passwd

    @classmethod
    def get_options(cls):
        return {
            "user":   Option(default=None, type=as_string_or_none, help="Site login"),
            "passwd": SecretOption(default=None, type=as_string_or_none, help="Site password"),
        }

    def login(self):
        raise NotImplementedError

    def _assert_auth(self, *args):
        _assert(AuthError, *args)  # pylint: disable=no-value-for-parameter


class WithCaptcha(BaseExtension):
    def __init__(self, captcha_decoder, **_):
        self._captcha_decoder = captcha_decoder


class WithScrape(BaseExtension):
    def __init__(self, client_agent, **_):
        self._client_agent = client_agent

    @classmethod
    def get_options(cls):
        return {
            "client_agent": Option(default="rtorrent/0.9.2/0.13.2", help="User-Agent for tracker"),
        }

    def _is_torrent_registered(self, base_scrape_url, torrent):
        # https://wiki.theory.org/BitTorrentSpecification#Tracker_.27scrape.27_Convention
        self._assert_match(torrent)  # pylint: disable=no-member
        data = self._read_url(  # pylint: disable=no-member
            url=urllib.parse.urljoin(base_scrape_url, "scrape.php?info_hash={}".format(torrent.get_scrape_hash())),
            headers={"User-Agent": self._client_agent},
        )
        return (len(tfile.decode_data(data).get("files", {})) == 0)


class WithTime(BaseExtension):
    def __init__(self, timezone, **_):
        self._default_timezone = timezone

    @classmethod
    def get_options(cls):
        return {
            "timezone": Option(
                default=None,
                type=as_string_or_none,
                help="Site timezone, is automatically detected if possible (or manually, 'Europe/Moscow' for example)",
            ),
        }

    def _select_tzinfo(self, site_timezone):
        if site_timezone is None or self._default_timezone is not None:
            return self._get_default_tzinfo()
        try:
            return pytz.timezone(site_timezone)
        except pytz.UnknownTimeZoneError:
            return self._get_default_tzinfo()

    def _get_default_tzinfo(self):
        msg = "Can't determine timezone of site, your must configure it manually"
        self._assert_logic(self._default_timezone is not None, msg)  # pylint: disable=no-member
        return pytz.timezone(self._default_timezone)
