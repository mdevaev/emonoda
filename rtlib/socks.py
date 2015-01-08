import urllib.request
import urllib.parse
import http.client
import socket

try:
    import socks
except ImportError:
    socks = None


# =====
SCHEME_TO_TYPE = {}
if socks is not None:
    SCHEME_TO_TYPE.update({
        "socks4": socks.PROXY_TYPE_SOCKS4,
        "socks5": socks.PROXY_TYPE_SOCKS5,
    })

SOCKS_PORT = 1080


# =====
class SocksHandler(urllib.request.HTTPHandler):
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        super().__init__(debuglevel=kwargs.pop("debuglevel", 0))

    def http_open(self, request):
        def build(host, port=None, strict=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT):  # pylint: disable=protected-access
            return _SocksConnection(*self._args, host=host, port=port, strict=strict, timeout=timeout, **self._kwargs)
        return self.do_open(build, request)


# =====
class _SocksConnection(http.client.HTTPConnection):
    def __init__(
        self,
        proxy_url=None,
        proxy_type=None,
        proxy_host=None,
        proxy_port=None,
        proxy_user=None,
        proxy_passwd=None,
        rdns=True,
        *args,
        **kwargs
    ):
        if socks is None:
            raise RuntimeError("Required module SocksiPy (the recommended is https://github.com/Anorov/PySocks)")
        kwargs.pop("strict", None)  # XXX: Fix for "TypeError: __init__() got an unexpected keyword argument 'strict'"
        super().__init__(*args, **kwargs)

        if proxy_url is not None:
            parsed = urllib.parse.urlparse(proxy_url)
            scheme = parsed.scheme
            proxy_user = parsed.username
            proxy_passwd = parsed.password
            proxy_host = parsed.hostname
            proxy_port = (parsed.port or SOCKS_PORT)
            proxy_type = SCHEME_TO_TYPE.get((scheme or "").lower())
            if proxy_type is None:
                raise RuntimeError("Invalid SOCKS protocol: {}".format(scheme))

        self._proxy_args = (proxy_type, proxy_host, proxy_port, rdns, proxy_user, proxy_passwd)

    def connect(self):
        self.sock = socks.socksocket()
        self.sock.setproxy(*self._proxy_args)
        if self.timeout is not socket._GLOBAL_DEFAULT_TIMEOUT:  # pylint: disable=protected-access
            self.sock.settimeout(self.timeout)
