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


import os
import pkgutil
import textwrap

import mako.template

from ...optconf import Option
from ...optconf.converters import as_string_or_none

from .. import BasePlugin
from .. import BaseExtension


# =====
def templated(name, built_in=True, **kwargs):
    if built_in:
        data = pkgutil.get_data(__name__, os.path.join("templates", name)).decode()
    else:
        with open(name) as template_file:
            data = template_file.read()
    template = textwrap.dedent(data).strip()
    return mako.template.Template(template).render(**kwargs).strip()


# =====
class BaseConfetti(BasePlugin):
    def __init__(self, timeout, retries, retries_sleep, **_):
        self._timeout = timeout
        self._retries = retries
        self._retries_sleep = retries_sleep

    @classmethod
    def get_options(cls):
        return {
            "timeout":       Option(default=10.0, help="Network timeout"),
            "retries":       Option(default=5, help="Retries for failed attempts"),
            "retries_sleep": Option(default=1.0, help="Sleep interval between failed attempts"),
        }

    def send_results(self, source, results):
        raise NotImplementedError


class WithProxy(BaseExtension):
    def __init__(self, proxy_url, **_):
        self._proxy_url = proxy_url

    @classmethod
    def get_options(cls):
        return {
            "proxy_url": Option(default=None, type=as_string_or_none, help="URL of HTTP/SOCKS4/SOCKS5 proxy"),
        }
