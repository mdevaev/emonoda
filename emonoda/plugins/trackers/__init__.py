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


import re
import socket
import urllib.request
import urllib.parse
import urllib.error
import http.client
import http.cookiejar
import json
import datetime

from typing import Dict
from typing import Pattern
from typing import Match
from typing import Callable
from typing import NamedTuple
from typing import Optional
from typing import Type
from typing import Any

import pytz

from ...optconf import Option
from ...optconf import SecretOption

from ...tfile import Torrent
from ...tfile import is_valid_torrent_data
from ...tfile import decode_torrent_data

from ... import web

from .. import BasePlugin
from .. import get_classes


# =====
class TrackerError(Exception):
    pass


class AuthError(TrackerError):
    pass


class LogicError(TrackerError):
    pass


class NetworkError(TrackerError):
    def __init__(self, sub: BaseException) -> None:
        super().__init__()
        self._sub = sub

    def __str__(self) -> str:
        return "{}: {}".format(type(self._sub).__name__, str(self._sub))


# =====
def _assert(exception: Type[TrackerError], arg: Any, msg: str="") -> None:
    if not arg:
        raise exception(msg)


class BaseTracker(BasePlugin):  # pylint: disable=too-many-instance-attributes
    _SITE_VERSION = 0
    _SITE_ENCODING = "utf-8"
    _SITE_RETRY_CODES = [500, 502, 503]

    _SITE_FINGERPRINT_URL = __D_SITE_FINGERPRINT_URL = ""
    _SITE_FINGERPRINT_TEXT = __D_SITE_FINGERPRINT_TEXT = ""

    _COMMENT_REGEXP = __D_COMMENT_REGEXP = re.compile(r"(?P<torrent_id>.*)")

    def __init__(  # pylint: disable=super-init-not-called
        self,
        timeout: float,
        retries: int,
        retries_sleep: float,
        user_agent: str,
        proxy_url: str,
        check_version: bool,
        check_fingerprint: bool,
        **_: Any,
    ) -> None:

        assert self._SITE_FINGERPRINT_URL != self.__D_SITE_FINGERPRINT_URL
        assert self._SITE_FINGERPRINT_TEXT != self.__D_SITE_FINGERPRINT_TEXT

        assert self._COMMENT_REGEXP.pattern != self.__D_COMMENT_REGEXP.pattern

        self.__timeout = timeout
        self.__retries = retries
        self.__retries_sleep = retries_sleep
        self.__user_agent = user_agent
        self.__proxy_url = proxy_url
        self.__check_version = check_version
        self.__check_fingerprint = check_fingerprint

        self.__opener: Optional[urllib.request.OpenerDirector] = None

        self.__cookie_jar: Optional[http.cookiejar.CookieJar] = None

    @classmethod
    def get_options(cls) -> Dict[str, Option]:
        return {
            "timeout":           Option(default=10.0, help="Timeout for HTTP client"),
            "retries":           Option(default=20, help="The number of retries to handle tracker-specific HTTP errors"),
            "retries_sleep":     Option(default=1.0, help="Sleep interval between failed retries"),
            "user_agent":        Option(default="Mozilla/5.0", help="User-Agent for site"),
            "proxy_url":         Option(default="", help="URL of HTTP/SOCKS4/SOCKS5 proxy"),
            "check_fingerprint": Option(default=True, help="Check the site fingerprint"),
            "check_version":     Option(default=True, help="Check the tracker version from GitHub"),
        }

    def test(self) -> None:
        if self.__check_fingerprint or self.__check_version:
            opener = web.build_opener(self.__proxy_url)
            info = self.__get_upstream_info(opener)
        if self.__check_fingerprint:
            self.__test_fingerprint(info["fingerprint"], opener)
        if self.__check_version:
            self.__test_version(info["version"])

    def is_matched_for(self, torrent: Torrent) -> bool:
        return (self._COMMENT_REGEXP.match(torrent.get_comment()) is not None)

    def fetch_new_data(self, torrent: Torrent) -> bytes:
        raise NotImplementedError

    # =====

    def _encode(self, arg: str) -> bytes:
        return arg.encode(self._SITE_ENCODING)

    def _decode(self, arg: bytes) -> str:
        return arg.decode(self._SITE_ENCODING)

    def _urlencode(self, arg: Dict) -> bytes:
        return self._encode(urllib.parse.urlencode(arg))

    # =====

    def _init_opener(self, with_cookies: bool) -> None:
        assert not self.__opener
        if with_cookies:
            self.__cookie_jar = http.cookiejar.CookieJar()
            self.__opener = web.build_opener(self.__proxy_url, self.__cookie_jar)
        else:
            self.__opener = web.build_opener(self.__proxy_url)

    def _set_cookie(self, name: str, value: str, **kwargs: Any) -> None:
        assert self.__cookie_jar
        params = {
            "version": 0,
            "port": None,
            "port_specified": False,
            "domain": "",
            "domain_specified": False,
            "domain_initial_dot": False,
            "path": "/",
            "path_specified": True,
            "secure": False,
            "expires": None,
            "discard": True,
            "comment": None,
            "comment_url": None,
            "rest": {"HttpOnly": None},
            "rfc2109": False,
        }
        params.update(kwargs)
        self.__cookie_jar.set_cookie(http.cookiejar.Cookie(  # type: ignore
            name=name,
            value=value,
            **params,
        ))

    def _read_url(self, *args: Any, **kwargs: Any) -> bytes:
        if not kwargs.get("opener"):
            kwargs["opener"] = self.__opener
        try:
            return self.__read_url_nofe(*args, **kwargs)
        except (
            socket.timeout,
            urllib.error.HTTPError,
            urllib.error.URLError,
            http.client.IncompleteRead,
            http.client.BadStatusLine,
            ConnectionResetError,
        ) as err:
            raise NetworkError(err)

    def __read_url_nofe(
        self,
        url: str,
        *,
        data: Optional[bytes]=None,
        headers: Optional[Dict[str, str]]=None,
        opener: urllib.request.OpenerDirector=None,
    ) -> bytes:

        assert opener
        headers = (headers or {})
        headers.setdefault("User-Agent", self.__user_agent)
        return web.read_url(
            opener=opener,
            url=url,
            data=data,
            headers=headers,
            timeout=self.__timeout,
            retries=self.__retries,
            retries_sleep=self.__retries_sleep,
            retry_codes=self._SITE_RETRY_CODES,
        )

    # =====

    def _assert_logic(self, arg: Any, *args: Any) -> None:
        _assert(LogicError, arg, *args)

    def _assert_logic_re_match(self, regexp: Pattern[str], text: str, msg: str) -> Match[str]:
        match = regexp.match(text)
        self._assert_logic(bool(match), msg)
        return match  # type: ignore

    def _assert_logic_re_search(self, regexp: Pattern[str], text: str, msg: str) -> Match[str]:
        match = regexp.search(text)
        self._assert_logic(bool(match), msg)
        return match  # type: ignore

    def _assert_match(self, torrent: Torrent) -> str:
        return self._assert_logic_re_match(
            regexp=self._COMMENT_REGEXP,
            text=torrent.get_comment(),
            msg="No match with torrent's comment",
        ).group("torrent_id")

    def _assert_valid_data(self, data: bytes, target: str="torrent") -> bytes:
        msg = "Received an invalid {} data: {} ...".format(target, repr(data[:20]))
        self._assert_logic(is_valid_torrent_data(data), msg)
        return data

    # =====

    def __get_upstream_info(self, opener: urllib.request.OpenerDirector) -> Dict:
        try:
            return json.loads(self.__read_url_nofe(
                url="https://raw.githubusercontent.com/mdevaev/emonoda/master/trackers/{}.json".format(self.PLUGIN_NAMES[0]),
                opener=opener,
            ).decode("utf-8"))
        except urllib.error.HTTPError as err:
            if err.code == 404:
                return self._get_local_info()
            raise

    @classmethod
    def _get_local_info(cls) -> Dict:  # Public for Makefile
        return {
            "version": cls._SITE_VERSION,
            "fingerprint": {
                "url":      cls._SITE_FINGERPRINT_URL,
                "encoding": cls._SITE_ENCODING,
                "text":     cls._SITE_FINGERPRINT_TEXT,
            },
        }

    def __test_fingerprint(self, fingerprint: Dict[str, str], opener: urllib.request.OpenerDirector) -> None:
        data = self._read_url(fingerprint["url"], opener=opener)
        msg = "Invalid site body, maybe tracker is blocked"
        try:
            page = data.decode(fingerprint["encoding"])
        except UnicodeDecodeError:
            raise TrackerError(msg)
        _assert(TrackerError, fingerprint["text"] in page, msg)

    def __test_version(self, upstream: int) -> None:
        _assert(
            TrackerError,
            self._SITE_VERSION >= upstream,
            "Tracker plugin is outdated (ver. local:{}, upstream:{}). I recommend to update the program".format(
                self._SITE_VERSION,
                upstream,
            ),
        )


class WithLogin(BaseTracker):
    def __init__(self, user: str, passwd: str, **_: Any) -> None:  # pylint: disable=super-init-not-called
        self._user = user
        self._passwd = passwd

    @classmethod
    def get_options(cls) -> Dict[str, Option]:
        return {
            "user":   Option(default="", help="Site login"),
            "passwd": SecretOption(default="", help="Site password"),
        }

    def login(self) -> None:
        raise NotImplementedError

    def _login_using_post(self, url: str, post: Dict[str, bytes], ok_text: str) -> None:
        self._assert_required_user_passwd()
        page = self._decode(self._read_url(url, data=self._urlencode(post)))
        self._assert_auth(ok_text in page, "Invalid user or password")

    def _assert_auth(self, *args: Any) -> None:
        _assert(AuthError, *args)  # pylint: disable=no-value-for-parameter

    def _assert_required_user_passwd(self) -> None:
        self._assert_auth(bool(self._user), "Required user for site")
        self._assert_auth(bool(self._passwd), "Required password for site")

    def _assert_auth_re_search(self, regexp: Pattern[str], text: str, msg: str) -> Match[str]:
        match = regexp.search(text)
        self._assert_auth(bool(match), msg)
        return match  # type: ignore


class WithCaptcha(BaseTracker):  # pylint: disable=abstract-method
    def __init__(self, captcha_decoder: Callable[[str], str], **_: Any) -> None:  # pylint: disable=super-init-not-called
        self._captcha_decoder = captcha_decoder


# =====
class WithCheckHash(BaseTracker):  # pylint: disable=abstract-method
    _TORRENT_HASH_URL = __D_TORRENT_HASH_URL = "{torrent_id}"
    _TORRENT_HASH_REGEXP = __D_TORRENT_HASH_REGEXP = re.compile(r"(?P<torrent_hash>.*)")

    def __init__(self, **_: Any) -> None:  # pylint: disable=super-init-not-called
        assert self._TORRENT_HASH_URL != self.__D_TORRENT_HASH_URL
        assert self._TORRENT_HASH_REGEXP.pattern != self.__D_TORRENT_HASH_REGEXP.pattern

    def fetch_hash(self, torrent: Torrent) -> str:
        torrent_id = self._assert_match(torrent)
        return self._assert_logic_re_search(
            regexp=self._TORRENT_HASH_REGEXP,
            text=self._decode(self._read_url(self._TORRENT_HASH_URL.format(torrent_id=torrent_id))),
            msg="Hash not found",
        ).group("torrent_hash").strip().lower()


class WithCheckScrape(BaseTracker):  # pylint: disable=abstract-method
    _TORRENT_SCRAPE_URL = __D_TORRENT_SCRAPE_URL = "{scrape_hash}"

    def __init__(self, client_agent: str, **_: Any) -> None:  # pylint: disable=super-init-not-called
        assert self._TORRENT_SCRAPE_URL != self.__D_TORRENT_SCRAPE_URL

        self._client_agent = client_agent

    @classmethod
    def get_options(cls) -> Dict[str, Option]:
        return {
            "client_agent": Option(default="rtorrent/0.9.2/0.13.2", help="User-Agent for tracker"),
        }

    def is_registered(self, torrent: Torrent) -> bool:
        # https://wiki.theory.org/BitTorrentSpecification#Tracker_.27scrape.27_Convention
        self._assert_match(torrent)
        data = self._assert_valid_data(self._read_url(
            url=self._TORRENT_SCRAPE_URL.format(scrape_hash=torrent.get_scrape_hash()),
            headers={"User-Agent": self._client_agent},
        ), target="scrape")
        return (len(decode_torrent_data(data).get("files", {})) != 0)


class WithCheckTime(BaseTracker):
    _TIMEZONE_URL = __D_TIMEZONE_URL = ""
    _TIMEZONE_REGEXP = __D_TIMEZONE_REGEXP = re.compile(r"(?P<torrent_hash>.*)")
    _TIMEZONE_PREFIX = __D_TIMEZONE_PREFIX = ""

    _TIMEZONE_STATIC = __D_TIMEZONE_STATIC = ""

    def __init__(self, timezone: str, **_: Any) -> None:  # pylint: disable=super-init-not-called
        assert (
            self._TIMEZONE_URL != self.__D_TIMEZONE_URL
            and self._TIMEZONE_REGEXP.pattern != self.__D_TIMEZONE_REGEXP.pattern
            and self._TIMEZONE_PREFIX != self.__D_TIMEZONE_PREFIX
        ) or self._TIMEZONE_STATIC != self.__D_TIMEZONE_STATIC

        self._default_timezone = timezone
        self._tzinfo: Optional[datetime.tzinfo] = None

    @classmethod
    def get_options(cls) -> Dict[str, Option]:
        return {
            "timezone": Option(
                default="",
                help="Site timezone, is automatically detected if possible (or manually, 'Europe/Moscow' for example)",
            ),
        }

    def init_tzinfo(self) -> None:
        timezone: Optional[str] = None
        if self._TIMEZONE_STATIC:
            timezone = self._TIMEZONE_STATIC
        else:
            page = self._decode(self._read_url(self._TIMEZONE_URL))
            timezone_match = self._TIMEZONE_REGEXP.search(page)
            if timezone_match is not None:
                timezone = self._TIMEZONE_PREFIX + timezone_match.group("timezone").replace(" ", "")
        self._tzinfo = self._select_tzinfo(timezone)

    def fetch_time(self, torrent: Torrent) -> int:
        raise NotImplementedError

    def _select_tzinfo(self, site_timezone: Optional[str]) -> datetime.tzinfo:
        if not site_timezone or self._default_timezone:
            return self.__get_default_tzinfo()
        try:
            return pytz.timezone(site_timezone)
        except pytz.UnknownTimeZoneError:  # type: ignore
            return self.__get_default_tzinfo()

    def __get_default_tzinfo(self) -> datetime.tzinfo:
        msg = "Can't determine timezone of site, your must configure it manually"
        self._assert_logic(bool(self._default_timezone), msg)
        return pytz.timezone(self._default_timezone)


# =====
class WithFetchByTorrentId(BaseTracker):
    _DOWNLOAD_URL = __D_DOWNLOAD_URL = "{torrent_id}"
    _DOWNLOAD_PAYLOAD: Optional[bytes] = None

    def __init__(self, **_: Any) -> None:  # pylint: disable=super-init-not-called
        assert self._DOWNLOAD_URL != self.__D_DOWNLOAD_URL

    def fetch_new_data(self, torrent: Torrent) -> bytes:
        torrent_id = self._assert_match(torrent)
        return self._assert_valid_data(self._read_url(
            url=self._DOWNLOAD_URL.format(torrent_id=torrent_id),
            data=self._DOWNLOAD_PAYLOAD,
        ))


class WithFetchByDownloadId(BaseTracker):
    _DOWNLOAD_ID_URL = __D_DOWNLOAD_ID_URL = "{torrent_id}"
    _DOWNLOAD_ID_REGEXP = __D_DOWNLOAD_ID_REGEXP = re.compile(r"(?P<download_id>.*)")
    _DOWNLOAD_URL = __D_DOWNLOAD_URL = "{download_id}"
    _DOWNLOAD_PAYLOAD: Optional[bytes] = None

    def __init__(self, **_: Any) -> None:  # pylint: disable=super-init-not-called
        assert self._DOWNLOAD_ID_URL != self.__D_DOWNLOAD_ID_URL
        assert self._DOWNLOAD_ID_REGEXP.pattern != self.__D_DOWNLOAD_ID_REGEXP.pattern
        assert self._DOWNLOAD_URL != self.__D_DOWNLOAD_URL

    def fetch_new_data(self, torrent: Torrent) -> bytes:
        torrent_id = self._assert_match(torrent)

        dl_id = self._assert_logic_re_search(
            regexp=self._DOWNLOAD_ID_REGEXP,
            text=self._decode(self._read_url(self._DOWNLOAD_ID_URL.format(torrent_id=torrent_id))),
            msg="Unknown download_id",
        ).group("download_id")

        return self._assert_valid_data(self._read_url(
            url=self._DOWNLOAD_URL.format(download_id=dl_id),
            data=self._DOWNLOAD_PAYLOAD,
        ))


class TrackerStat(NamedTuple):
    seeders: int = 0
    leechers: int = 0


class WithStat(BaseTracker):  # pylint: disable=abstract-method
    _STAT_URL = __D_STAT_URL = "{torrent_id}"
    _STAT_OK_REGEXP = __D_STAT_OK_REGEXP = re.compile(r".*")
    _STAT_SEEDERS_REGEXP = __D_STAT_SEEDERS_REGEXP = re.compile(r"(?P<seeders>.*)")
    _STAT_LEECHERS_REGEXP = __D_STAT_LEECHERS_REGEXP = re.compile(r"(?P<leechers>.*)")

    def __init__(self, **_: Any) -> None:  # pylint: disable=super-init-not-called
        assert self._STAT_URL != self.__D_STAT_URL
        assert self._STAT_OK_REGEXP.pattern != self.__D_STAT_OK_REGEXP.pattern
        assert self._STAT_SEEDERS_REGEXP.pattern != self.__D_STAT_SEEDERS_REGEXP.pattern
        assert self._STAT_LEECHERS_REGEXP.pattern != self.__D_STAT_LEECHERS_REGEXP.pattern

    def fetch_stat(self, torrent: Torrent) -> TrackerStat:
        torrent_id = self._assert_match(torrent)
        page = self._decode(self._read_url(self._STAT_URL.format(torrent_id=torrent_id)))
        self._assert_logic_re_search(
            regexp=self._STAT_OK_REGEXP,
            text=page,
            msg="Missing OK mark",
        )
        return TrackerStat(
            seeders=self.__parse_stat_int(page, self._STAT_SEEDERS_REGEXP, "seeders"),
            leechers=self.__parse_stat_int(page, self._STAT_LEECHERS_REGEXP, "leechers"),
        )

    def __parse_stat_int(self, page: str, regexp: Pattern, group: str) -> int:
        match = regexp.search(page)
        if match:
            return int(match.group(group))
        return 0


# =====
def get_tracker_class(name: str) -> Type[BaseTracker]:
    return get_classes("trackers")[name]  # type: ignore
