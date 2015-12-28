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
    PLUGIN_NAME = "ktorrent"

    def __init__(self, **kwargs):  # pylint: disable=super-init-not-called
        self._init_bases(**kwargs)

        if dbus is None:
            raise RuntimeError("Required module dbus")

        self._bus = dbus.SessionBus()
        self._core = self._bus.get_object("org.ktorrent.ktorrent", "/core")
        self._settings = self._bus.get_object("org.ktorrent.ktorrent", "/settings")

        if self._settings.useSaveDir():
            raise RuntimeError("Turn off the path by default in the settings of KTorrent")

    @classmethod
    def get_options(cls):
        return cls._get_merged_options()

    # ===

    @hash_or_torrent
    def remove_torrent(self, torrent_hash):
        self._get_torrent_obj(torrent_hash)  # XXX: raise NoSuchTorrentError if torrent does not exist
        self._core.remove(torrent_hash, False)

    @check_torrent_accessible
    def load_torrent(self, torrent, prefix=None):
        if prefix is not None:
            self._settings.setLastSaveDir(prefix)
        self._core.loadSilently(torrent.get_path(), "")

    @hash_or_torrent
    def has_torrent(self, torrent_hash):
        try:
            self._get_torrent_obj(torrent_hash)
            return True
        except NoSuchTorrentError:
            return False

    def get_hashes(self):
        return list(map(str.lower, self._core.torrents()))

    @hash_or_torrent
    def get_torrent_path(self, torrent_hash):
        raise RuntimeError("KTorrent can not return a path of the torrent file")

    @hash_or_torrent
    def get_data_prefix(self, torrent_hash):
        return str(self._get_torrent_obj(torrent_hash).dataDir())

    def get_data_prefix_default(self):
        raise RuntimeError("KTorrent can not return a default data path")

    # ===

    @hash_or_torrent
    def get_full_path(self, torrent_hash):
        return str(self._get_torrent_obj(torrent_hash).pathOnDisk())

    @hash_or_torrent
    def get_file_name(self, torrent_hash):
        return str(self._get_torrent_obj(torrent_hash).name())

    @hash_or_torrent
    def is_single_file(self, torrent_hash):
        return (self._get_torrent_obj(torrent_hash).numFiles() == 0)

    @hash_or_torrent
    def get_files(self, torrent_hash, on_fs=False):
        torrent_obj = self._get_torrent_obj(torrent_hash)
        prefix = (str(torrent_obj.pathOnDisk()) if on_fs else "")
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
        return build_files(prefix, flist)

    # ===

    def _get_torrent_obj(self, torrent_hash):
        if torrent_hash not in self.get_hashes():
            raise NoSuchTorrentError("Unknown torrent hash")
        try:
            torrent_obj = self._bus.get_object("org.ktorrent.ktorrent", "/torrent/" + torrent_hash)
            assert str(torrent_obj.infoHash()) == torrent_hash
            return torrent_obj
        except dbus.exceptions.DBusException as err:
            if err.get_dbus_name() == "org.freedesktop.DBus.Error.UnknownObject":
                raise NoSuchTorrentError("Unknown torrent hash")
            raise
