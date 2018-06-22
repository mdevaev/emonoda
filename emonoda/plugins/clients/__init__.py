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

from typing import Tuple
from typing import List
from typing import Dict
from typing import Callable
from typing import Union
from typing import Type
from typing import Any

from ...tfile import TorrentEntryAttrs
from ...tfile import Torrent

from .. import BasePlugin
from .. import get_classes


# =====
class NoSuchTorrentError(Exception):
    pass


# =====
def hash_or_torrent(method: Callable) -> Callable:
    def wrap(self: "BaseClient", torrent: Union[Torrent, str], *args: Any, **kwargs: Any) -> Any:
        torrent_hash = (torrent.get_hash() if isinstance(torrent, Torrent) else torrent)
        return method(self, torrent_hash, *args, **kwargs)
    return wrap


def check_torrent_accessible(method: Callable) -> Callable:
    def wrap(self: "BaseClient", torrent: Torrent, prefix: str="") -> Any:
        path = torrent.get_path()
        assert path is not None, "Required Torrent() with local file"
        open(path, "rb").close()  # Check accessible file
        if prefix:
            os.listdir(prefix)  # Check accessible prefix
        return method(self, torrent, prefix)
    return wrap


def build_files(prefix: str, flist: List[Tuple[str, int]]) -> Dict[str, TorrentEntryAttrs]:
    files: Dict[str, TorrentEntryAttrs] = {}
    for (path, size) in flist:
        path_list = path.split(os.path.sep)
        name = None
        for index in range(len(path_list)):
            name = os.path.join(prefix, os.path.sep.join(path_list[0:index + 1]))
            files[name] = TorrentEntryAttrs.dir()
        assert name is not None
        files[name] = TorrentEntryAttrs.file(size)
    return files


class BaseClient(BasePlugin):
    def __init__(self, **_: Any) -> None:  # pylint: disable=super-init-not-called
        pass

    @hash_or_torrent
    def remove_torrent(self, torrent_hash: str) -> None:
        raise NotImplementedError

    @check_torrent_accessible
    def load_torrent(self, torrent: Torrent, prefix: str) -> None:
        raise NotImplementedError

    def get_hashes(self) -> List[str]:
        raise NotImplementedError

    @hash_or_torrent
    def has_torrent(self, torrent_hash: str) -> bool:
        raise NotImplementedError

    @hash_or_torrent
    def get_data_prefix(self, torrent_hash: str) -> str:
        raise NotImplementedError

    def get_data_prefix_default(self) -> str:
        raise NotImplementedError

    # =====

    @hash_or_torrent
    def get_full_path(self, torrent_hash: str) -> str:
        raise NotImplementedError

    @hash_or_torrent
    def get_file_name(self, torrent_hash: str) -> str:
        raise NotImplementedError

    @hash_or_torrent
    def get_files(self, torrent_hash: str) -> Dict[str, TorrentEntryAttrs]:
        raise NotImplementedError


class WithCustoms(BaseClient):
    def __init__(self, **_: Any) -> None:  # pylint: disable=super-init-not-called
        pass

    @classmethod
    def get_custom_keys(cls) -> List[str]:
        raise NotImplementedError

    @hash_or_torrent
    def set_customs(self, torrent_hash: str, customs: Dict[str, str]) -> None:
        raise NotImplementedError

    @hash_or_torrent
    def get_customs(self, torrent_hash: str, keys: List[str]) -> Dict[str, str]:
        raise NotImplementedError


# =====
def get_client_class(name: str) -> Type[BaseClient]:
    return get_classes("clients")[name]  # type: ignore
