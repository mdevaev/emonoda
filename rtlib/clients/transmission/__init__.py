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


import os
import transmissionrpc

from ...optconf import (
    Option,
    SecretOption,
)
from ...core import client


# =====
class Client(client.BaseClient):
    # API description:
    #   http://pythonhosted.org/transmissionrpc/
    #   https://trac.transmissionbt.com/browser/trunk/extras/rpc-spec.txt

    def __init__(self, url, user, passwd, timeout):
        self._client = transmissionrpc.Client(
            address=url,
            user=user,
            password=passwd,
            timeout=timeout,
        )

    @classmethod
    def get_name(cls):
        return "transmission"

    @classmethod
    def get_options(cls):
        return {
            "url":     Option(default="http://localhost:9091/transmission/rpc", help="Transmission HTTP-RPC URL"),
            "timeout": Option(default=10.0, type=float, help="Timeout for HTTP-RPC"),
            "user":    Option(default=None, type=str, help="HTTP login"),
            "passwd":  SecretOption(default=None, type=str, help="HTTP password"),
        }

    # ===

    @client.hash_or_torrent
    def remove_torrent(self, torrent_hash):
        self._get_torrent_obj(torrent_hash)  # XXX: raise client.NoSuchTorrentError if torrent does not exist
        self._client.remove_torrent(torrent_hash)

    @client.check_torrent_accessible
    def load_torrent(self, torrent, prefix=None):
        torrent_path = torrent.get_path()
        kwargs = {"paused": False}
        if prefix is not None:
            kwargs["download_dir"] = prefix
        self._client.add_torrent(torrent_path, **kwargs)

    @client.hash_or_torrent
    def has_torrent(self, torrent_hash):
        try:
            self._get_torrent_obj(torrent_hash)
            return True
        except client.NoSuchTorrentError:
            return False

    def get_hashes(self):
        return [
            str(item.hashString.lower())
            for item in self._client.get_torrents(arguments=("id", "hashString"))
        ]

    @client.hash_or_torrent
    def get_torrent_path(self, torrent_hash):
        return self._get_torrent_prop(torrent_hash, "torrentFile")

    @client.hash_or_torrent
    def get_data_prefix(self, torrent_hash):
        return self._get_torrent_prop(torrent_hash, "downloadDir")

    def get_data_prefix_default(self):
        session = self._client.get_session()
        assert session is not None
        return session.download_dir

    # ===

    @client.hash_or_torrent
    def get_full_path(self, torrent_hash):
        torrent_obj = self._get_torrent_obj(torrent_hash, ("name", "downloadDir"))
        return os.path.join(torrent_obj.downloadDir, torrent_obj.name)

    @client.hash_or_torrent
    def get_file_name(self, torrent_hash):
        return self._get_torrent_prop(torrent_hash, "name")

    @client.hash_or_torrent
    def is_single_file(self, torrent_hash):
        files = self._get_files(torrent_hash)
        if len(files) > 1:
            return False
        return (os.path.sep not in list(files.values())[0]["name"])

    @client.hash_or_torrent
    def get_files(self, torrent_hash, on_fs=False):
        prefix = (self.get_data_prefix(torrent_hash) if on_fs else "")
        flist = [
            (item["name"], item["size"])
            for item in self._get_files(torrent_hash).values()
        ]
        return client.build_files(prefix, flist)

    # ===

    def _get_torrent_prop(self, torrent_hash, prop):
        return getattr(self._get_torrent_obj(torrent_hash, (prop,)), prop)

    def _get_torrent_obj(self, torrent_hash, props=()):
        props = set(props).union(("id", "hashString"))
        try:
            torrent_obj = self._client.get_torrent(torrent_hash, arguments=tuple(props))
        except KeyError as err:
            if str(err) == "\'Torrent not found in result\'":
                raise client.NoSuchTorrentError("Unknown torrent hash")
            raise
        assert str(torrent_obj.hashString).lower() == torrent_hash
        return torrent_obj

    def _get_files(self, torrent_hash):
        files = self._client.get_files(torrent_hash)
        if len(files) == 0:
            raise client.NoSuchTorrentError("Unknown torrent hash")
        assert len(files) == 1
        files = list(files.values())[0]
        assert len(files) > 0
        return files
