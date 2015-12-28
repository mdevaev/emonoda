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

from ...optconf import Option

from . import BaseClient
from . import WithCustoms
from . import NoSuchTorrentError
from . import hash_or_torrent
from . import check_torrent_accessible
from . import build_files


# =====
_XMLRPC_UNKNOWN_HASH = -501


# =====
def _catch_unknown_torrent(method):
    def wrap(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except xmlrpc.client.Fault as err:
            if err.faultCode == _XMLRPC_UNKNOWN_HASH:
                raise NoSuchTorrentError("Unknown torrent hash")
            raise
    return wrap


class Plugin(BaseClient, WithCustoms):
    # API description: http://code.google.com/p/gi-torrent/wiki/rTorrent_XMLRPC_reference

    PLUGIN_NAME = "rtorrent"

    def __init__(self, url, load_retries, retries_sleep, xmlrpc_size_limit, **kwargs):  # pylint:disable=super-init-not-called
        self._init_bases(**kwargs)

        self._load_retries = load_retries
        self._retries_sleep = retries_sleep
        self._server = xmlrpc.client.ServerProxy(url)
        self._server.set_xmlrpc_size_limit(xmlrpc_size_limit)

    @classmethod
    def get_options(cls):
        return cls._get_merged_options({
            "url":               Option(default="http://localhost/RPC2", help="XMLRPC mountpoint"),
            "load_retries":      Option(default=10, help="The number of retries to load the torrent"),
            "retries_sleep":     Option(default=1.0, help="Sleep interval between the load retries"),
            "xmlrpc_size_limit": Option(default=67108863, help="Max XMLRPC data size"),
        })

    # ===

    @hash_or_torrent
    @_catch_unknown_torrent
    def remove_torrent(self, torrent_hash):
        self._server.d.erase(torrent_hash)

    @check_torrent_accessible
    def load_torrent(self, torrent, prefix=None):
        torrent_hash = torrent.get_hash()
        # XXX: https://github.com/rakshasa/rtorrent/issues/22
        # All load_* calls re asynchronous, so we need to wait until the load of torrent files is complete.
        self._server.load_raw(torrent.get_data())
        retries = self._load_retries
        while True:
            try:
                assert self._server.d.get_hash(torrent_hash).lower() == torrent_hash
                break
            except xmlrpc.client.Fault as err:
                if err.faultCode != _XMLRPC_UNKNOWN_HASH:
                    raise
                if retries == 0:
                    raise RuntimeError("Timed out torrent uploads after {} seconds".format(
                        self._load_retries * self._retries_sleep))
                retries -= 1
                time.sleep(self._retries_sleep)

        if prefix is not None:
            self._server.d.set_directory(torrent_hash, prefix)
        self._server.d.start(torrent_hash)

    @hash_or_torrent
    def has_torrent(self, torrent_hash):
        try:
            assert self._server.d.get_hash(torrent_hash).lower() == torrent_hash
            return True
        except xmlrpc.client.Fault as err:
            if err.faultCode != _XMLRPC_UNKNOWN_HASH:
                raise
        return False

    def get_hashes(self):
        return list(map(str.lower, self._server.download_list()))

    @hash_or_torrent
    @_catch_unknown_torrent
    def get_torrent_path(self, torrent_hash):
        return self._server.d.get_loaded_file(torrent_hash)

    @hash_or_torrent
    @_catch_unknown_torrent
    def get_data_prefix(self, torrent_hash):
        mc = xmlrpc.client.MultiCall(self._server)
        mc.d.get_directory(torrent_hash)
        mc.d.is_multi_file(torrent_hash)
        (path, is_multi_file) = mc()
        if is_multi_file:
            path = os.path.dirname(os.path.normpath(path))
        return path

    def get_data_prefix_default(self):
        return self._server.get_directory()

    # ===

    @hash_or_torrent
    @_catch_unknown_torrent
    def get_full_path(self, torrent_hash):
        return self._server.d.get_base_path(torrent_hash)

    @hash_or_torrent
    @_catch_unknown_torrent
    def get_file_name(self, torrent_hash):
        return self._server.d.get_name(torrent_hash)

    @hash_or_torrent
    @_catch_unknown_torrent
    def is_single_file(self, torrent_hash):
        return (not self._server.d.is_multi_file(torrent_hash))

    @hash_or_torrent
    @_catch_unknown_torrent
    def get_files(self, torrent_hash, on_fs=False):
        mc = xmlrpc.client.MultiCall(self._server)
        mc.d.get_base_path(torrent_hash)
        mc.d.get_base_filename(torrent_hash)
        mc.d.is_multi_file(torrent_hash)
        mc.d.get_size_files(torrent_hash)
        mc.f.get_size_bytes(torrent_hash, 0)
        (base_path, base_file_name, is_multi_file, count, first_file_size) = tuple(mc())
        base = (base_path if on_fs else base_file_name)

        if not is_multi_file:
            return {base: {"size": first_file_size}}

        mc = xmlrpc.client.MultiCall(self._server)
        for index in range(count):
            mc.f.get_path(torrent_hash, index)
            mc.f.get_size_bytes(torrent_hash, index)
        flist = tuple(mc())
        flist = tuple(zip(flist[::2], flist[1::2]))

        files = build_files(base, flist)
        files.update({base: None})
        return files

    # ===

    @classmethod
    def get_custom_keys(cls):
        return ("c1", "c2", "c3", "c4", "c5")

    @hash_or_torrent
    @_catch_unknown_torrent
    def set_customs(self, torrent_hash, customs):
        assert len(customs) != 0, "Empty customs dict"
        mc = xmlrpc.client.MultiCall(self._server)
        for (key, value) in customs.items():
            getattr(mc.d, "set_custom{}".format(key[1:]))(torrent_hash, value)
        mc()

    @hash_or_torrent
    @_catch_unknown_torrent
    def get_customs(self, torrent_hash, keys):
        assert len(keys) != 0, "Empty customs keys list"
        keys = tuple(set(keys))
        mc = xmlrpc.client.MultiCall(self._server)
        for key in keys:
            getattr(mc.d, "get_custom{}".format(key[1:]))(torrent_hash)
        return dict(zip(keys, tuple(mc())))
