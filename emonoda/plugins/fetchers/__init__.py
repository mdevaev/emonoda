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


import json
import socket
import urllib.request
import urllib.parse
import http.cookiejar
import http.client
import time

from ...optconf import Option
from ...optconf import SecretOption

from ... import tfile
from ... import sockshandler

from .. import BasePlugin
from .. import BaseExtension


# =====
class FetcherError(Exception):
    pass


class AuthError(FetcherError):
    pass


class LogicError(FetcherError):
    pass


class TypicalNetworkError(FetcherError):
    def __init__(self, err):
        super().__init__()
        self.err = err

    def __str__(self):
        return "{}: {}".format(type(self.err).__name__, str(self.err))


# =====
def select_fetcher(torrent, fetchers):
    for fetcher in fetchers:
        if fetcher.is_matched_for(torrent):
            return fetcher
    return None


# =====
def build_opener(proxy_url=None, cookie_jar=None):
    handlers = []

    if proxy_url is not None:
        scheme = (urllib.parse.urlparse(proxy_url).scheme or "").lower()
        if scheme == "http":
            proxies = dict.fromkeys(("http", "https"), proxy_url)
            handlers.append(urllib.request.ProxyHandler(proxies))
        elif scheme in ("socks4", "socks5"):
            handlers.append(sockshandler.SocksHandler(proxy_url=proxy_url))
        else:
            raise RuntimeError("Invalid proxy protocol: {}".format(scheme))

    if cookie_jar is not None:
        handlers.append(urllib.request.HTTPCookieProcessor(cookie_jar))

    return urllib.request.build_opener(*handlers)


def read_url(
    opener,
    url,
    data=None,
    headers=None,
    timeout=10,
    retries=10,
    sleep_time=1,
    retry_codes=(500, 502, 503),
    retry_timeout=True,
):
    while True:
        try:
            request = urllib.request.Request(url, data, (headers or {}))
            return opener.open(request, timeout=timeout).read()
        except socket.timeout as err:
            if retries == 0 or not retry_timeout:
                raise TypicalNetworkError(err)
        except urllib.error.HTTPError as err:
            if retries == 0 or err.code not in retry_codes:
                raise TypicalNetworkError(err)
        except urllib.error.URLError as err:
            if isinstance(err.reason, str) and "timed out" in err.reason:
                if retries == 0 or not retry_timeout:
                    raise TypicalNetworkError(err)
            else:
                raise
        except (http.client.IncompleteRead, http.client.BadStatusLine, ConnectionResetError) as err:
            if retries == 0:
                raise TypicalNetworkError(err)
        time.sleep(sleep_time)
        retries -= 1


# =====
def _assert(exception, arg, msg=""):
    if not arg:
        raise exception(msg)


class BaseFetcher(BasePlugin):  # pylint: disable=too-many-instance-attributes
    def __init__(self, url_retries, url_sleep_time, timeout, user_agent, client_agent, proxy_url, check_version, **_):
        self._url_retries = url_retries
        self._url_sleep_time = url_sleep_time
        self._timeout = timeout
        self._user_agent = user_agent
        self._client_agent = client_agent
        self._proxy_url = proxy_url
        self._check_version = check_version

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
            "url_retries":    Option(default=20, help="The number of retries to handle tracker-specific HTTP errors"),
            "url_sleep_time": Option(default=1.0, help="Sleep interval between the retries"),
            "timeout":        Option(default=10.0, type=float, help="Timeout for HTTP client"),
            "user_agent":     Option(default="Mozilla/5.0", help="User-agent for site"),
            "client_agent":   Option(default="rtorrent/0.9.2/0.13.2", help="User-agent for tracker"),
            "proxy_url":      Option(default=None, type=str, help="The URL of the HTTP proxy"),
            "check_version":  Option(default=True, help="Check the fetcher version from GitHub")
        }

    def is_torrent_changed(self, torrent):
        raise NotImplementedError

    def fetch_new_data(self, torrent):
        raise NotImplementedError

    # ===

    def _init_opener(self, with_cookies):
        if with_cookies:
            self._cookie_jar = http.cookiejar.CookieJar()
            self._opener = build_opener(self._proxy_url, self._cookie_jar)
        else:
            self._opener = build_opener(self._proxy_url)

    def _build_opener(self):
        return build_opener(self._proxy_url)

    def _read_url(self, url, data=None, headers=None, opener=None):
        opener = (opener or self._opener)
        assert opener is not None

        headers = (headers or {})
        headers.setdefault("User-Agent", self._user_agent)

        return read_url(
            opener=opener,
            url=url,
            data=data,
            headers=headers,
            timeout=self._timeout,
            retries=self._url_retries,
            sleep_time=self._url_sleep_time,
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
        opener = build_opener(self._proxy_url)
        info = self._get_upstream_info(opener)
        self._test_fingerprint(info["fingerprint"], opener)
        if self._check_version:
            self._test_version(info["version"])

    def _get_upstream_info(self, opener):
        return json.loads(self._read_url(
            url="https://raw.githubusercontent.com/mdevaev/emonoda/master/fetchers.json",
            opener=opener,
        ).decode("utf-8"))[self.get_name()]

    def _test_fingerprint(self, fingerprint, opener):
        text = self._read_url(fingerprint["url"], opener=opener).decode(fingerprint["encoding"])
        _assert(FetcherError, fingerprint["text"] in text, "Invalid site body, maybe tracker is blocked")

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
            "user":   Option(default=None, type=str, help="Site login"),
            "passwd": SecretOption(default=None, type=str, help="Site password"),
        }

    def login(self):
        raise NotImplementedError

    def _assert_auth(self, *args):
        _assert(AuthError, *args)


class WithCaptcha(BaseExtension):
    def __init__(self, captcha_decoder, **_):
        self._captcha_decoder = captcha_decoder
