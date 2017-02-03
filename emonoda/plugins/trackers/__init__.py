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
class TrackerError(Exception):
    pass


class AuthError(TrackerError):
    pass


class LogicError(TrackerError):
    pass


class NetworkError(TrackerError):
    def __init__(self, sub):
        super().__init__()
        self._sub = sub

    def __str__(self):
        return "{}: {}".format(type(self._sub).__name__, str(self._sub))


# =====
def _assert(exception, arg, msg=""):
    if not arg:
        raise exception(msg)


class BaseTracker(BasePlugin):  # pylint: disable=too-many-instance-attributes
    _SITE_VERSION = None
    _SITE_ENCODING = None
    _SITE_RETRY_CODES = (500, 502, 503)

    _SITE_FINGERPRINT_URL = None
    _SITE_FINGERPRINT_TEXT = None

    _COMMENT_REGEXP = None

    def __init__(self, timeout, retries, retries_sleep, user_agent, proxy_url,
                 check_version, check_fingerprint, **_):

        assert self._SITE_VERSION is not None
        assert self._SITE_ENCODING is not None
        assert self._SITE_FINGERPRINT_URL is not None
        assert self._SITE_FINGERPRINT_TEXT is not None

        assert self._COMMENT_REGEXP is not None

        self._timeout = timeout
        self._retries = retries
        self._retries_sleep = retries_sleep
        self._user_agent = user_agent
        self._proxy_url = proxy_url
        self._check_version = check_version
        self._check_fingerprint = check_fingerprint

        self._cookie_jar = None
        self._opener = None

    @classmethod
    def get_options(cls):
        return {
            "timeout":           Option(default=10.0, help="Timeout for HTTP client"),
            "retries":           Option(default=20, help="The number of retries to handle tracker-specific HTTP errors"),
            "retries_sleep":     Option(default=1.0, help="Sleep interval between failed retries"),
            "user_agent":        Option(default="Mozilla/5.0", help="User-Agent for site"),
            "proxy_url":         Option(default=None, type=as_string_or_none, help="URL of HTTP/SOCKS4/SOCKS5 proxy"),
            "check_fingerprint": Option(default=True, help="Check the site fingerprint"),
            "check_version":     Option(default=True, help="Check the tracker version from GitHub"),
        }

    def test(self):
        if self._check_fingerprint or self._check_version:
            opener = web.build_opener(self._proxy_url)
            info = self._get_upstream_info(opener)
        if self._check_fingerprint:
            self._test_fingerprint(info["fingerprint"], opener)
        if self._check_version:
            self._test_version(info["version"])

    def is_matched_for(self, torrent):
        assert self._COMMENT_REGEXP is not None
        return (self._COMMENT_REGEXP.match(torrent.get_comment() or "") is not None)

    # ===

    def _encode(self, arg):
        return arg.encode(self._SITE_ENCODING)

    def _decode(self, arg):
        return arg.decode(self._SITE_ENCODING)

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
            retry_codes=self._SITE_RETRY_CODES,
        )

    # ===

    def _assert_logic(self, arg, *args):
        _assert(LogicError, arg, *args)

    def _assert_match(self, torrent):
        self._assert_logic(self.is_matched_for(torrent), "No match with torrent")

    def _assert_valid_data(self, data):
        msg = "Received an invalid torrent data: {} ...".format(repr(data[:20]))
        self._assert_logic(tfile.is_valid_data(data), msg)

    # ===

    def _get_upstream_info(self, opener):
        try:
            return json.loads(self._read_url_nofe(
                url="https://raw.githubusercontent.com/mdevaev/emonoda/master/trackers/{}.json".format(self.PLUGIN_NAME),
                opener=opener,
            ).decode("utf-8"))
        except urllib.error.HTTPError as err:
            if err.code == 404:
                return self._get_local_info()
            raise

    @classmethod
    def _get_local_info(cls):
        return {
            "version": cls._SITE_VERSION,
            "fingerprint": {
                "url":      cls._SITE_FINGERPRINT_URL,
                "encoding": cls._SITE_ENCODING,
                "text":     cls._SITE_FINGERPRINT_TEXT,
            },
        }

    def _test_fingerprint(self, fingerprint, opener):
        data = self._read_url(fingerprint["url"], opener=opener)
        msg = "Invalid site body, maybe tracker is blocked"
        try:
            page = data.decode(fingerprint["encoding"])
        except UnicodeDecodeError:
            raise TrackerError(msg)
        _assert(TrackerError, fingerprint["text"] in page, msg)

    def _test_version(self, upstream):
        _assert(
            TrackerError,
            self._SITE_VERSION >= upstream,
            "Tracker plugin is outdated (ver. local:{}, upstream:{}). I recommend to update the program".format(
                self._SITE_VERSION,
                upstream,
            ),
        )


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

    def _login_using_post(self, url, post, ok_text):
        self._assert_required_user_passwd()
        page = self._decode(self._read_url(url, data=self._encode(urllib.parse.urlencode(post))))  # pylint: disable=no-member
        self._assert_auth(ok_text in page, "Invalid user or password")

    def _assert_auth(self, *args):
        _assert(AuthError, *args)  # pylint: disable=no-value-for-parameter

    def _assert_required_user_passwd(self):
        self._assert_auth(self._user is not None, "Required user for site")
        self._assert_auth(self._passwd is not None, "Required password for site")


class WithCaptcha(BaseExtension):
    def __init__(self, captcha_decoder, **_):
        self._captcha_decoder = captcha_decoder


# =====
class WithCheckHash(BaseExtension):
    _TORRENT_HASH_URL = None
    _TORRENT_HASH_REGEXP = None

    def __init__(self, **_):
        assert self._TORRENT_HASH_URL is not None
        assert self._TORRENT_HASH_REGEXP is not None

    def fetch_hash(self, torrent):
        # pylint: disable=no-member
        self._assert_match(torrent)

        torrent_id = self._COMMENT_REGEXP.match(torrent.get_comment()).group("torrent_id")

        page = self._decode(self._read_url(self._TORRENT_HASH_URL.format(torrent_id=torrent_id)))
        hash_match = self._TORRENT_HASH_REGEXP.search(page)
        self._assert_logic(hash_match is not None, "Hash not found")
        return hash_match.group("torrent_hash").strip().lower()


class WithCheckScrape(BaseExtension):
    _TORRENT_SCRAPE_URL = None

    def __init__(self, client_agent, **_):
        assert self._TORRENT_SCRAPE_URL is not None

        self._client_agent = client_agent

    @classmethod
    def get_options(cls):
        return {
            "client_agent": Option(default="rtorrent/0.9.2/0.13.2", help="User-Agent for tracker"),
        }

    def is_registered(self, torrent):
        # https://wiki.theory.org/BitTorrentSpecification#Tracker_.27scrape.27_Convention
        self._assert_match(torrent)  # pylint: disable=no-member
        data = self._read_url(  # pylint: disable=no-member
            url=self._TORRENT_SCRAPE_URL.format(scrape_hash=torrent.get_scrape_hash()),
            headers={"User-Agent": self._client_agent},
        )

        msg = "Received an invalid scrape data: {} ...".format(repr(data[:20]))
        self._assert_logic(tfile.is_valid_data(data), msg)  # pylint: disable=no-member
        return (len(tfile.decode_data(data).get("files", {})) != 0)


class WithCheckTime(BaseExtension):
    _TIMEZONE_URL = None
    _TIMEZONE_REGEXP = None
    _TIMEZONE_PREFIX = None

    _TIMEZONE_STATIC = None

    def __init__(self, timezone, **_):
        assert (
            self._TIMEZONE_URL is not None
            and self._TIMEZONE_REGEXP is not None
            and self._TIMEZONE_PREFIX is not None
        ) or self._TIMEZONE_STATIC is not None

        self._default_timezone = timezone
        self._tzinfo = None

    @classmethod
    def get_options(cls):
        return {
            "timezone": Option(
                default=None,
                type=as_string_or_none,
                help="Site timezone, is automatically detected if possible (or manually, 'Europe/Moscow' for example)",
            ),
        }

    def init_tzinfo(self):
        if self._TIMEZONE_STATIC is not None:
            timezone = self._TIMEZONE_STATIC
        else:
            page = self._decode(self._read_url(self._TIMEZONE_URL))  # pylint: disable=no-member
            timezone_match = self._TIMEZONE_REGEXP.search(page)
            timezone = (timezone_match and self._TIMEZONE_PREFIX + timezone_match.group("timezone").replace(" ", ""))
        self._tzinfo = self._select_tzinfo(timezone)

    def fetch_time(self, torrent):
        raise NotImplementedError

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


# =====
class WithFetchByTorrentId(BaseExtension):
    _DOWNLOAD_URL = None
    _DOWNLOAD_PAYLOAD = None

    def __init__(self, **_):
        assert self._DOWNLOAD_URL is not None

    def fetch_new_data(self, torrent):
        # pylint: disable=no-member
        self._assert_match(torrent)

        torrent_id = self._COMMENT_REGEXP.match(torrent.get_comment()).group("torrent_id")

        data = self._read_url(self._DOWNLOAD_URL.format(torrent_id=torrent_id), data=self._DOWNLOAD_PAYLOAD)
        self._assert_valid_data(data)
        return data


class WithFetchByDownloadId(BaseExtension):
    _DOWNLOAD_ID_URL = None
    _DOWNLOAD_ID_REGEXP = None
    _DOWNLOAD_URL = None
    _DOWNLOAD_PAYLOAD = None

    def __init__(self, **_):
        assert self._DOWNLOAD_ID_URL is not None
        assert self._DOWNLOAD_ID_REGEXP is not None
        assert self._DOWNLOAD_URL is not None

    def fetch_new_data(self, torrent):
        # pylint: disable=no-member
        self._assert_match(torrent)

        torrent_id = self._COMMENT_REGEXP.match(torrent.get_comment()).group("torrent_id")
        page = self._decode(self._read_url(self._DOWNLOAD_ID_URL.format(torrent_id=torrent_id)))

        dl_id_match = self._DOWNLOAD_ID_REGEXP.search(page)
        self._assert_logic(dl_id_match is not None, "Unknown download_id")
        dl_id = dl_id_match.group("download_id")

        data = self._read_url(self._DOWNLOAD_URL.format(download_id=dl_id), data=self._DOWNLOAD_PAYLOAD)
        self._assert_valid_data(data)
        return data


class WithFetchCustom(BaseExtension):
    def __init__(self, **_):
        pass

    def fetch_new_data(self, torrent):
        raise NotImplementedError
