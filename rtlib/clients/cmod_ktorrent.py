#####
#
#    KTorrent client for rtfetch
#    Copyright (C) 2013  Devaev Maxim <mdevaev@gmail.com>
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
try :
    import dbus # pylint: disable=F0401
except ImportError :
    dbus = None # pylint: disable=C0103

from .. import clientlib


##### Public constants #####
CLIENT_NAME = "ktorrent"


##### Public classes #####
class Client(clientlib.AbstractClient) :
    def __init__(self, url = None) :
        if dbus is None :
            raise RuntimeError("Required module dbus")
        if url is not None :
            raise RuntimeError("The argument \"url\" is not used by this module")

        self._bus = dbus.SessionBus()
        self._core = self._bus.get_object("org.ktorrent.ktorrent", "/core")
        self._settings = self._bus.get_object("org.ktorrent.ktorrent", "/settings")

        if self._settings.useSaveDir() :
            raise RuntimeError("Turn off the path by default in the settings of KTorrent")

        clientlib.AbstractClient.__init__(self, url)


    ### Public ###

    @classmethod
    def plugin(cls) :
        return CLIENT_NAME

    ###

    @clientlib.hashOrTorrent
    def removeTorrent(self, torrent_hash) :
        self._getTorrent(torrent_hash) # XXX: raise clientlib.NoSuchTorrentError for non-existent torrent
        self._core.remove(torrent_hash, False)

    @clientlib.loadTorrentAccessible
    def loadTorrent(self, torrent, prefix = None) :
        if prefix is not None :
            self._settings.setLastSaveDir(prefix)
        self._core.loadSilently(torrent.path(), "")

    @clientlib.hashOrTorrent
    def hasTorrent(self, torrent_hash) :
        try :
            self._getTorrent(torrent_hash)
            return True
        except clientlib.NoSuchTorrentError :
            return False

    def hashes(self) :
        return list(map(str.lower, self._core.torrents(utf8_strings=True)))

    @clientlib.hashOrTorrent
    def torrentPath(self, torrent_hash) :
        raise RuntimeError("KTorrent can not return the path to the torrent file")

    @clientlib.hashOrTorrent
    def dataPrefix(self, torrent_hash) :
        return str(self._getTorrent(torrent_hash).dataDir(utf8_strings=True))

    def defaultDataPrefix(self) :
        raise RuntimeError("KTorrent can not return the default data path")

    ###

    @clientlib.hashOrTorrent
    def fullPath(self, torrent_hash) :
        return str(self._getTorrent(torrent_hash).pathOnDisk(utf8_strings=True))

    @clientlib.hashOrTorrent
    def name(self, torrent_hash) :
        return str(self._getTorrent(torrent_hash).name(utf8_strings=True))

    @clientlib.hashOrTorrent
    def isSingleFile(self, torrent_hash) :
        return ( self._getTorrent(torrent_hash).numFiles() == 0 )

    @clientlib.hashOrTorrent
    def files(self, torrent_hash, system_path_flag = False) :
        torrent_obj = self._getTorrent(torrent_hash)
        prefix = ( str(torrent_obj.pathOnDisk(utf8_strings=True)) if system_path_flag else "" )
        count = torrent_obj.numFiles()
        name = str(torrent_obj.name(utf8_strings=True))
        if count == 0 : # Single file
            files_list = [(name, int(torrent_obj.totalSize()))]
        else :
            files_list = [ (
                    os.path.join(name, str(torrent_obj.filePath(dbus.UInt32(index), utf8_strings=True))),
                    int(torrent_obj.fileSize(dbus.UInt32(index))),
                ) for index in range(count) ]
        return clientlib.buildFiles(prefix, files_list)


    ### Private ###

    def _getTorrent(self, torrent_hash) :
        if torrent_hash not in self.hashes() :
            raise clientlib.NoSuchTorrentError("Unknown torrent hash")
        try :
            torrent_obj = self._bus.get_object("org.ktorrent.ktorrent", "/torrent/" + torrent_hash)
            assert str(torrent_obj.infoHash()) == torrent_hash
            return torrent_obj
        except dbus.exceptions.DBusException as err :
            if err.get_dbus_name() == "org.freedesktop.DBus.Error.UnknownObject" :
                raise clientlib.NoSuchTorrentError("Unknown torrent hash")
            raise

