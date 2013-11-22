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


import socket
import urllib.request
import urllib.parse
import urllib.error
import json
import time

from ulib import network
import ulib.network.url # pylint: disable=W0611

from . import const
from . import tfile


##### Public constants #####
DEFAULT_LOGIN = ""
DEFAULT_PASSWD = ""
DEFAULT_URL_RETRIES = 10
DEFAULT_URL_SLEEP_TIME = 1
DEFAULT_RETRY_CODES = (503, 502, 500)
DEFAULT_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1"
DEFAULT_CLIENT_AGENT = "rtorrent/0.9.2/0.13.2"
DEFAULT_PROXY_URL = None
DEFAULT_INTERACTIVE_FLAG = False

VERSIONS_URL = const.RAW_UPSTREAM_URL + "/fetchers.json"


##### Exceptions #####
class CommonFetcherError(Exception) :
    pass

class SiteError(CommonFetcherError) :
    pass

class LoginError(CommonFetcherError) :
    pass

class FetcherError(CommonFetcherError) :
    pass


##### Public methods #####
def selectFetcher(torrent, fetchers_list) :
    for fetcher in fetchers_list :
        if fetcher.match(torrent) :
            return fetcher
    return None


###
def buildTypicalOpener(cookie_jar = None, proxy_url = None) :
    handlers_list = []
    if not cookie_jar is None :
        handlers_list.append(urllib.request.HTTPCookieProcessor(cookie_jar))
    if not proxy_url is None :
        scheme = ( urllib.parse.urlparse(proxy_url).scheme or "" ).lower()
        if scheme == "http" :
            handlers_list.append(urllib.request.ProxyHandler({
                    "http"  : proxy_url,
                    "https" : proxy_url,
                }))
        elif scheme in ("socks4", "socks5") :
            handlers_list.append(network.url.SocksHandler(proxy_url=proxy_url))
        else :
            raise RuntimeError("Invalid proxy protocol: %s" % (scheme))
    return urllib.request.build_opener(*handlers_list)

def readUrlRetry(
        opener,
        url,
        data = None,
        headers_dict = None,
        timeout = socket._GLOBAL_DEFAULT_TIMEOUT, # pylint: disable=W0212
        retries = DEFAULT_URL_RETRIES,
        sleep_time = DEFAULT_URL_SLEEP_TIME,
        retry_codes_list = DEFAULT_RETRY_CODES,
        retry_timeout_flag = True,
    ) :

    while True :
        try :
            request = urllib.request.Request(url, data, ( headers_dict or {} ))
            return opener.open(request, timeout=timeout).read()
        except (socket.timeout, urllib.error.URLError, urllib.error.HTTPError) as err :
            if retries == 0 :
                raise
            if isinstance(err, socket.timeout) or isinstance(err, urllib.error.URLError) and err.reason == "timed out" :
                if not retry_timeout_flag :
                    raise
            elif isinstance(err, urllib.error.HTTPError) :
                if not err.code in retry_codes_list :
                    raise
            retries -= 1
            time.sleep(sleep_time)


###
def checkVersions(fetchers_list) :
    versions_dict = json.loads(urllib.request.urlopen(VERSIONS_URL).read().decode("utf-8"))
    ok_flag = True
    for fetcher in fetchers_list :
        plugin_name = fetcher.plugin()
        local_version = fetcher.version()
        if not plugin_name in versions_dict :
            continue
        upstream_version = versions_dict[plugin_name]["version"]
        if local_version < upstream_version :
            print("# Plug-in \"%s\" is outdated." % (plugin_name))
            print("#    Local version:    %d" % (local_version))
            print("#    Upstream version: %d" % (upstream_version))
            print("# The plugin can not work properly. It is recommended to upgrade the program.")
            ok_flag = False
    return ok_flag


##### Public classes #####
class AbstractFetcher :
    def __init__(self, user_name, passwd, url_retries, url_sleep_time, timeout, user_agent, client_agent, proxy_url, interactive_flag, captcha_callback) :
        self.__user_name        = self.__assertIsInstance(user_name,        str)
        self.__passwd           = self.__assertIsInstance(passwd,           str)
        self.__url_retries      = self.__assertIsInstance(url_retries,      int)
        self.__url_sleep_time   = self.__assertIsInstance(url_sleep_time,   (int, float))
        self.__timeout          = self.__assertIsInstance(timeout,          (int, float))
        self.__user_agent       = self.__assertIsInstance(user_agent,       (str, type(None)))
        self.__client_agent     = self.__assertIsInstance(client_agent,     (str, type(None)))
        self.__proxy_url        = self.__assertIsInstance(proxy_url,        (str, type(None)))
        self.__interactive_flag = self.__assertIsInstance(interactive_flag, bool)

        assert callable(captcha_callback)
        self.__captcha_callback = captcha_callback


    ### Public ###

    @classmethod
    def plugin(cls) :
        raise NotImplementedError

    @classmethod
    def version(cls) :
        raise NotImplementedError

    ###

    def match(self, torrent) :
        raise NotImplementedError

    def ping(self) :
        raise NotImplementedError

    def login(self) :
        raise NotImplementedError

    def loggedIn(self) :
        raise NotImplementedError

    def torrentChanged(self, torrent) :
        raise NotImplementedError

    def fetchTorrent(self, torrent) :
        raise NotImplementedError

    ###

    def userName(self) :
        return self.__user_name

    def passwd(self) :
        return self.__passwd

    def urlRetries(self) :
        return self.__url_retries

    def urlSleepTime(self) :
        return self.__url_sleep_time

    def timeout(self) :
        return self.__timeout

    def userAgent(self) :
        return self.__user_agent

    def clientAgent(self) :
        return self.__client_agent

    def proxyUrl(self) :
        return self.__proxy_url

    def isInteractive(self) :
        return self.__interactive_flag

    def decodeCaptcha(self, url) :
        return self.__captcha_callback(url)

    ###

    def assertSite(self, arg) :
        self.__customAssert(SiteError, arg, "Invalid site body, maybe site is blocked")

    def assertLogin(self, *args_list) :
        self.__customAssert(LoginError, *args_list)

    def assertFetcher(self, *args_list) :
        self.__customAssert(FetcherError, *args_list)

    def assertNonAnonymous(self) :
        self.assertLogin(len(self.__user_name) != 0, "The tracker \"%s\" can not be used anonymously" % (self.plugin()))

    def assertMatch(self, torrent) :
        self.assertFetcher(self.match(torrent), "No comment match")

    def assertValidTorrentData(self, data) :
        message = "Received an invalid torrent data: %s ..." % (repr(data[:20]))
        self.assertFetcher(tfile.isValidTorrentData(data), message)


    ### Private ###

    def __customAssert(self, exception, arg, message = "") :
        if not arg :
            raise exception(message)

    ###

    def __assertIsInstance(self, value, value_type) :
        assert isinstance(value, value_type)
        return value

