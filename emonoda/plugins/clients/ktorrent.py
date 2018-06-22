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

from typing import List
from typing import Dict
from typing import Any

from ...optconf import Option

from ...tfile import TorrentEntryAttrs
from ...tfile import Torrent

from . import BaseClient
from . import NoSuchTorrentError
from . import hash_or_torrent
from . import check_torrent_accessible
from . import build_files

try:
    import dbus  # pylint: disable=import-error
except ImportError:
    dbus = None


# =====
class Plugin(BaseClient):
    PLUGIN_NAMES = ["ktorrent"]

    def __init__(self, service: str, **kwargs: Any) -> None:  # pylint: disable=super-init-not-called
        self._init_bases(**kwargs)

        if dbus is None:
            raise RuntimeError("Required module dbus")

        self.__service = service

        self.__bus = dbus.SessionBus()
        self.__core = self.__bus.get_object(self.__service, "/core")
        self.__settings = self.__bus.get_object(self.__service, "/settings")

        if self.__settings.useSaveDir():
            raise RuntimeError("Turn off the 'path by default' in KTorrent settings")

    @classmethod
    def get_options(cls) -> Dict[str, Option]:
        return cls._get_merged_options({
            "service": Option(default="org.kde.ktorrent", help="D-Bus service, use 'org.ktorrent.ktorrent' for old client"),
        })

    # =====

    @hash_or_torrent
    def remove_torrent(self, torrent_hash: str) -> None:
        self.__get_torrent_obj(torrent_hash)  # XXX: raise NoSuchTorrentError if torrent does not exist
        self.__core.remove(torrent_hash, False)

    @check_torrent_accessible
    def load_torrent(self, torrent: Torrent, prefix: str) -> None:
        self.__settings.setLastSaveDir(prefix)
        self.__core.loadSilently(torrent.get_path(), "")

    @hash_or_torrent
    def has_torrent(self, torrent_hash: str) -> bool:
        try:
            self.__get_torrent_obj(torrent_hash)
            return True
        except NoSuchTorrentError:
            return False

    def get_hashes(self) -> List[str]:
        return list(map(str.lower, self.__core.torrents()))

    @hash_or_torrent
    def get_data_prefix(self, torrent_hash: str) -> str:
        return str(self.__get_torrent_obj(torrent_hash).dataDir())

    def get_data_prefix_default(self) -> str:
        return str(self.__settings.saveDir())

    # =====

    @hash_or_torrent
    def get_full_path(self, torrent_hash: str) -> str:
        return str(self.__get_torrent_obj(torrent_hash).pathOnDisk())

    @hash_or_torrent
    def get_file_name(self, torrent_hash: str) -> str:
        return str(self.__get_torrent_obj(torrent_hash).name())

    @hash_or_torrent
    def get_files(self, torrent_hash: str) -> Dict[str, TorrentEntryAttrs]:
        torrent_obj = self.__get_torrent_obj(torrent_hash)
        count = torrent_obj.numFiles()
        name = str(torrent_obj.name())
        if count == 0:  # Single file
            flist = [(name, int(torrent_obj.totalSize()))]
        else:
            flist = [
                (
                    os.path.join(name, str(torrent_obj.filePath(dbus.UInt32(index)))),
                    int(torrent_obj.fileSize(dbus.UInt32(index))),
                )
                for index in range(count)
            ]
        return build_files("", flist)

    # =====

    def __get_torrent_obj(self, torrent_hash: str) -> Any:
        if torrent_hash not in self.get_hashes():
            raise NoSuchTorrentError("Unknown torrent hash")
        try:
            torrent_obj = self.__bus.get_object(self.__service, "/torrent/" + torrent_hash)
            assert str(torrent_obj.infoHash()) == torrent_hash
            return torrent_obj
        except dbus.exceptions.DBusException as err:
            if err.get_dbus_name() == "org.freedesktop.DBus.Error.UnknownObject":
                raise NoSuchTorrentError("Unknown torrent hash")
            raise
