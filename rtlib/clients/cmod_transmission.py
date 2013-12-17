#####
#
#    transmission client for rtfetch
#    Copyright (C) 2013  Vitaly Lipatov <lav@etersoft.ru>, Devaev Maxim <mdevaev@gmail.com>
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
    import transmissionrpc # pylint: disable=F0401
except ImportError :
    transmissionrpc = None # pylint: disable=C0103

from .. import clientlib


##### Public constants #####
CLIENT_NAME = "transmission"
DEFAULT_URL = "http://localhost:9091/transmission/rpc"


##### Public classes #####
class Client(clientlib.AbstractClient) :
    # XXX: API description:
    #   http://pythonhosted.org/transmissionrpc/
    #   https://trac.transmissionbt.com/browser/trunk/extras/rpc-spec.txt

    def __init__(self, url = DEFAULT_URL) :
        if transmissionrpc is None :
            raise RuntimeError("Required module transmissionrpc")
        if url is None :
            url = DEFAULT_URL

        # Client uses urlparse for get user and password from URL
        self._server = transmissionrpc.Client(url)

        clientlib.AbstractClient.__init__(self, url)


    ### Public ###

    @classmethod
    def plugin(cls) :
        return CLIENT_NAME

    ###

    @clientlib.hashOrTorrent
    def removeTorrent(self, torrent_hash) :
        self._getTorrent(torrent_hash) # XXX: raise clientlib.NoSuchTorrentError for non-existent torrent
        self._server.remove_torrent(torrent_hash)

    @clientlib.loadTorrentAccessible
    def loadTorrent(self, torrent, prefix = None) :
        torrent_path = torrent.path()
        kwargs_dict = { "paused" : False }
        if prefix is not None :
            kwargs_dict["download_dir"] = prefix
        self._server.add_torrent(torrent_path, **kwargs_dict)

    @clientlib.hashOrTorrent
    def hasTorrent(self, torrent_hash) :
        try :
            self._getTorrent(torrent_hash)
            return True
        except clientlib.NoSuchTorrentError :
            return False

    def hashes(self) :
        return [ str(item.hashString.lower()) for item in self._server.get_torrents(arguments=("id", "hashString")) ]

    @clientlib.hashOrTorrent
    def torrentPath(self, torrent_hash) :
        return self._getTorrentArg(torrent_hash, "torrentFile")

    @clientlib.hashOrTorrent
    def dataPrefix(self, torrent_hash) :
        return self._getTorrentArg(torrent_hash, "downloadDir")

    def defaultDataPrefix(self) :
        session = self._server.get_session()
        assert session is not None
        return session.download_dir

    ###

    @clientlib.hashOrTorrent
    def fullPath(self, torrent_hash) :
        torrent_obj = self._getTorrent(torrent_hash, ("name", "downloadDir"))
        return os.path.join(torrent_obj.downloadDir, torrent_obj.name)

    @clientlib.hashOrTorrent
    def name(self, torrent_hash) :
        return self._getTorrentArg(torrent_hash, "name")

    @clientlib.hashOrTorrent
    def isSingleFile(self, torrent_hash) :
        files_dict = self._getFiles(torrent_hash)
        if len(files_dict) > 1 :
            return False
        return ( os.path.sep not in list(files_dict.values())[0]["name"] )

    @clientlib.hashOrTorrent
    def files(self, torrent_hash, system_path_flag = False) :
        prefix = ( self.dataPrefix(torrent_hash) if system_path_flag else "" )
        files_list = [
            (item["name"], item["size"])
            for item in list(self._getFiles(torrent_hash).values())
        ]
        return clientlib.buildFiles(prefix, files_list)


    ### Private ###

    def _getTorrentArg(self, torrent_hash, arg_name) :
        return getattr(self._getTorrent(torrent_hash, (arg_name,)), arg_name)

    def _getTorrent(self, torrent_hash, args_list = ()) :
        args_set = set(args_list).union(("id", "hashString"))
        try :
            torrent_obj = self._server.get_torrent(torrent_hash, arguments=tuple(args_set))
        except KeyError as err :
            if str(err) == "\'Torrent not found in result\'" :
                raise clientlib.NoSuchTorrentError("Unknown torrent hash")
            raise
        assert str(torrent_obj.hashString).lower() == torrent_hash
        return torrent_obj

    def _getFiles(self, torrent_hash) :
        files_dict = self._server.get_files(torrent_hash)
        if len(files_dict) == 0 :
            raise clientlib.NoSuchTorrentError("Unknown torrent hash")
        assert len(files_dict) == 1
        files_dict = list(files_dict.values())[0]
        assert len(files_dict) > 0
        return files_dict

