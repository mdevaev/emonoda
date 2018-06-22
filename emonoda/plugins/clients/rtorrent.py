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
import time
import xmlrpc.client

from typing import List
from typing import Dict
from typing import Callable
from typing import Any

from ...optconf import Option

from ...tfile import TorrentEntryAttrs
from ...tfile import Torrent

from . import WithCustoms
from . import NoSuchTorrentError
from . import hash_or_torrent
from . import check_torrent_accessible
from . import build_files


# =====
_XMLRPC_UNKNOWN_HASH = -501


def _catch_unknown_torrent(method: Callable) -> Callable:
    def wrap(self: WithCustoms, *args: Any, **kwargs: Any) -> Any:
        try:
            return method(self, *args, **kwargs)
        except xmlrpc.client.Fault as err:
            if err.faultCode == _XMLRPC_UNKNOWN_HASH:
                raise NoSuchTorrentError("Unknown torrent hash")
            raise
    return wrap


# =====
class Plugin(WithCustoms):
    # API description: http://code.google.com/p/gi-torrent/wiki/rTorrent_XMLRPC_reference

    PLUGIN_NAMES = ["rtorrent"]

    def __init__(  # pylint:disable=super-init-not-called
        self,
        url: str,
        load_retries: int,
        retries_sleep: float,
        xmlrpc_size_limit: int,
        **kwargs: Any,
    ) -> None:

        self._init_bases(**kwargs)

        self.__load_retries = load_retries
        self.__retries_sleep = retries_sleep
        self.__server = xmlrpc.client.ServerProxy(url)
        self.__server.set_xmlrpc_size_limit(xmlrpc_size_limit)

    @classmethod
    def get_options(cls) -> Dict[str, Option]:
        return cls._get_merged_options({
            "url":               Option(default="http://localhost/RPC2", help="XMLRPC mountpoint"),
            "load_retries":      Option(default=10, help="The number of retries to load the torrent"),
            "retries_sleep":     Option(default=1.0, help="Sleep interval between the load retries"),
            "xmlrpc_size_limit": Option(default=67108863, help="Max XMLRPC data size"),
        })

    # =====

    @hash_or_torrent
    @_catch_unknown_torrent
    def remove_torrent(self, torrent_hash: str) -> None:
        self.__server.d.erase(torrent_hash)

    @check_torrent_accessible
    def load_torrent(self, torrent: Torrent, prefix: str) -> None:
        torrent_hash = torrent.get_hash()
        # XXX: https://github.com/rakshasa/rtorrent/issues/22
        # All load_* calls re asynchronous, so we need to wait until the load of torrent files is complete.
        self.__server.load_raw(torrent.get_data())
        retries = self.__load_retries
        while True:
            try:
                assert self.__server.d.get_hash(torrent_hash).lower() == torrent_hash
                break
            except xmlrpc.client.Fault as err:
                if err.faultCode != _XMLRPC_UNKNOWN_HASH:
                    raise
                if retries == 0:
                    raise RuntimeError("Timed out torrent uploads after {} seconds".format(
                        self.__load_retries * self.__retries_sleep))
                retries -= 1
                time.sleep(self.__retries_sleep)

        self.__server.d.set_directory(torrent_hash, prefix)
        self.__server.d.start(torrent_hash)

    @hash_or_torrent
    def has_torrent(self, torrent_hash: str) -> bool:
        try:
            assert self.__server.d.get_hash(torrent_hash).lower() == torrent_hash
            return True
        except xmlrpc.client.Fault as err:
            if err.faultCode != _XMLRPC_UNKNOWN_HASH:
                raise
        return False

    def get_hashes(self) -> List[str]:
        return list(map(str.lower, self.__server.download_list()))

    @hash_or_torrent
    @_catch_unknown_torrent
    def get_data_prefix(self, torrent_hash: str) -> str:
        mc = xmlrpc.client.MultiCall(self.__server)
        mc.d.get_directory(torrent_hash)
        mc.d.is_multi_file(torrent_hash)
        (path, is_multi_file) = mc()
        if is_multi_file:
            path = os.path.dirname(os.path.normpath(path))
        return path

    def get_data_prefix_default(self) -> str:
        return self.__server.get_directory()

    # =====

    @hash_or_torrent
    @_catch_unknown_torrent
    def get_full_path(self, torrent_hash: str) -> str:
        mc = xmlrpc.client.MultiCall(self.__server)
        mc.d.get_directory(torrent_hash)
        mc.d.get_name(torrent_hash)
        mc.d.is_multi_file(torrent_hash)
        (path, name, is_multi_file) = mc()
        if is_multi_file:
            return path
        return os.path.join(path, name)

    @hash_or_torrent
    @_catch_unknown_torrent
    def get_file_name(self, torrent_hash: str) -> str:
        return self.__server.d.get_name(torrent_hash)

    @hash_or_torrent
    @_catch_unknown_torrent
    def get_files(self, torrent_hash: str) -> Dict[str, TorrentEntryAttrs]:
        mc = xmlrpc.client.MultiCall(self.__server)
        mc.d.get_base_filename(torrent_hash)
        mc.d.is_multi_file(torrent_hash)
        mc.d.get_size_files(torrent_hash)
        mc.f.get_size_bytes(torrent_hash, 0)
        (base_file_name, is_multi_file, count, first_file_size) = tuple(mc())

        if not is_multi_file:
            return {base_file_name: TorrentEntryAttrs.file(first_file_size)}

        mc = xmlrpc.client.MultiCall(self.__server)
        for index in range(count):
            mc.f.get_path(torrent_hash, index)
            mc.f.get_size_bytes(torrent_hash, index)
        flist = list(mc())
        flist = list(zip(flist[::2], flist[1::2]))

        files = build_files(base_file_name, flist)
        files.update({base_file_name: TorrentEntryAttrs.dir()})
        return files

    # =====

    @classmethod
    def get_custom_keys(cls) -> List[str]:
        return ["c1", "c2", "c3", "c4", "c5"]

    @hash_or_torrent
    @_catch_unknown_torrent
    def set_customs(self, torrent_hash: str, customs: Dict[str, str]) -> None:
        assert len(customs) != 0, "Empty customs dict"
        mc = xmlrpc.client.MultiCall(self.__server)
        for (key, value) in customs.items():
            getattr(mc.d, "set_custom{}".format(key[1:]))(torrent_hash, value)
        mc()

    @hash_or_torrent
    @_catch_unknown_torrent
    def get_customs(self, torrent_hash: str, keys: List[str]) -> Dict[str, str]:
        assert len(keys) != 0, "Empty customs keys list"
        keys = list(set(keys))
        mc = xmlrpc.client.MultiCall(self.__server)
        for key in keys:
            getattr(mc.d, "get_custom{}".format(key[1:]))(torrent_hash)
        return dict(zip(keys, list(mc())))
