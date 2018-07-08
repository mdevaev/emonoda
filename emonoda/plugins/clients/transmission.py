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
import base64

from typing import List
from typing import Dict
from typing import Optional
from typing import Any

from ...optconf import Option
from ...optconf import SecretOption

from ...tfile import TorrentEntryAttrs
from ...tfile import Torrent

from . import BaseClient
from . import NoSuchTorrentError
from . import hash_or_torrent
from . import check_torrent_accessible
from . import build_files

try:
    import transmissionrpc
except ImportError:
    transmissionrpc = None


# =====
class Plugin(BaseClient):
    # API description:
    #   http://pythonhosted.org/transmissionrpc/
    #   https://trac.transmissionbt.com/browser/trunk/extras/rpc-spec.txt

    PLUGIN_NAMES = ["transmission"]

    def __init__(  # pylint: disable=super-init-not-called
        self,
        url: str,
        user: str,
        passwd: str,
        timeout: float,
        **kwargs: Any,
    ) -> None:

        self._init_bases(**kwargs)

        if transmissionrpc is None:
            raise RuntimeError("Required module transmissionrpc")

        self._client = transmissionrpc.Client(
            address=url,
            user=(user or None),
            password=(passwd or None),
            timeout=timeout,
        )

    @classmethod
    def get_options(cls) -> Dict[str, Option]:
        return cls._get_merged_options({
            "url":     Option(default="http://localhost:9091/transmission/rpc", help="Transmission HTTP-RPC URL"),
            "timeout": Option(default=10.0, help="Timeout for HTTP-RPC"),
            "user":    Option(default="", help="HTTP login"),
            "passwd":  SecretOption(default="", help="HTTP password"),
        })

    # =====

    @hash_or_torrent
    def remove_torrent(self, torrent_hash: str) -> None:
        self.__get_torrent_obj(torrent_hash)  # XXX: raise NoSuchTorrentError if torrent does not exist
        self._client.remove_torrent(torrent_hash)

    @check_torrent_accessible
    def load_torrent(self, torrent: Torrent, prefix: str) -> None:
        self._client.add_torrent(
            base64.b64encode(torrent.get_data()).decode("utf-8"),
            download_dir=prefix,
            paused=False,
        )

    @hash_or_torrent
    def has_torrent(self, torrent_hash: str) -> bool:
        try:
            self.__get_torrent_obj(torrent_hash)
            return True
        except NoSuchTorrentError:
            return False

    def get_hashes(self) -> List[str]:
        return [
            str(item.hashString.lower())
            for item in self._client.get_torrents(arguments=("id", "hashString"))
        ]

    @hash_or_torrent
    def get_data_prefix(self, torrent_hash: str) -> str:
        return self.__get_torrent_prop(torrent_hash, "downloadDir")

    def get_data_prefix_default(self) -> str:
        session = self._client.get_session()
        assert session is not None
        return session.download_dir

    # =====

    @hash_or_torrent
    def get_full_path(self, torrent_hash: str) -> str:
        torrent_obj = self.__get_torrent_obj(torrent_hash, ["name", "downloadDir"])
        return os.path.join(torrent_obj.downloadDir, torrent_obj.name)

    @hash_or_torrent
    def get_file_name(self, torrent_hash: str) -> str:
        return self.__get_torrent_prop(torrent_hash, "name")

    @hash_or_torrent
    def get_files(self, torrent_hash: str) -> Dict[str, TorrentEntryAttrs]:
        flist = [
            (item["name"], item["size"])
            for item in self.__get_files(torrent_hash).values()
        ]
        return build_files("", flist)

    # =====

    def __get_torrent_prop(self, torrent_hash: str, prop: str) -> Any:
        return getattr(self.__get_torrent_obj(torrent_hash, [prop]), prop)

    def __get_torrent_obj(self, torrent_hash: str, props: Optional[List[str]]=None) -> Any:
        props = list(set(props or []).union(["id", "hashString"]))
        try:
            torrent_obj = self._client.get_torrent(torrent_hash, arguments=props)
        except KeyError as err:
            if str(err) == "\'Torrent not found in result\'":
                raise NoSuchTorrentError("Unknown torrent hash")
            raise
        assert str(torrent_obj.hashString).lower() == torrent_hash
        return torrent_obj

    def __get_files(self, torrent_hash: str) -> Dict:
        files = self._client.get_files(torrent_hash)
        if len(files) == 0:
            raise NoSuchTorrentError("Unknown torrent hash")
        assert len(files) == 1
        files = list(files.values())[0]
        assert len(files) > 0
        return files
