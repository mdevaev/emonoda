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
import xmlrpc.client
import time

from .. import clientlib


##### Public constants #####
CLIENT_NAME = "rtorrent"
DEFAULT_URL = "http://localhost/RPC2"

XMLRPC_SIZE_LIMIT = 67108863
LOAD_RETRIES = 10
LOAD_RETRIES_SLEEP = 1

FAULT_CODE_UNKNOWN_HASH = -501


##### Private methods #####
def _catchUnknownTorrentFault(method) :
    def wrap(self, *args_list, **kwargs_dict) :
        try :
            return method(self, *args_list, **kwargs_dict)
        except xmlrpc.client.Fault as err :
            if err.faultCode == FAULT_CODE_UNKNOWN_HASH :
                raise clientlib.NoSuchTorrentError("Unknown torrent hash")
            raise
    return wrap


##### Public classes #####
class Client(clientlib.AbstractClient) :
    # XXX: API description: http://code.google.com/p/gi-torrent/wiki/rTorrent_XMLRPC_reference

    def __init__(self, url = DEFAULT_URL) :
        if url is None :
            url = DEFAULT_URL
        self._server = xmlrpc.client.ServerProxy(url)
        self._server.set_xmlrpc_size_limit(XMLRPC_SIZE_LIMIT)
        clientlib.AbstractClient.__init__(self, url)


    ### Public ###

    @classmethod
    def plugin(cls) :
        return CLIENT_NAME

    ###

    @clientlib.hashOrTorrent
    @_catchUnknownTorrentFault
    def removeTorrent(self, torrent_hash) :
        self._server.d.erase(torrent_hash)

    @clientlib.loadTorrentAccessible
    def loadTorrent(self, torrent, prefix = None) :
        torrent_path = torrent.path()
        torrent_hash = torrent.hash()

        # XXX: https://github.com/rakshasa/rtorrent/issues/22
        # All load_* calls re asynchronous, so we need to wait until the load of torrent files is complete.
        self._server.load(torrent_path)
        retries = LOAD_RETRIES
        while True :
            try :
                assert self._server.d.get_hash(torrent_hash).lower() == torrent_hash
                break
            except xmlrpc.client.Fault as err :
                if err.faultCode != FAULT_CODE_UNKNOWN_HASH :
                    raise
                if retries == 0 :
                    raise RuntimeError("Timed torrent uploads after %d seconds" % (LOAD_RETRIES * LOAD_RETRIES_SLEEP))
                retries -= 1
                time.sleep(LOAD_RETRIES_SLEEP)

        if prefix is not None :
            self._server.d.set_directory(torrent_hash, prefix)
        self._server.d.start(torrent_hash)

    @clientlib.hashOrTorrent
    def hasTorrent(self, torrent_hash) :
        try :
            assert self._server.d.get_hash(torrent_hash).lower() == torrent_hash
            return True
        except xmlrpc.client.Fault as err :
            if err.faultCode != FAULT_CODE_UNKNOWN_HASH :
                raise
        return False

    def hashes(self) :
        return list(map(str.lower, self._server.download_list()))

    @clientlib.hashOrTorrent
    @_catchUnknownTorrentFault
    def torrentPath(self, torrent_hash) :
        return self._server.d.get_loaded_file(torrent_hash)

    @clientlib.hashOrTorrent
    @_catchUnknownTorrentFault
    def dataPrefix(self, torrent_hash) :
        multicall = xmlrpc.client.MultiCall(self._server)
        multicall.d.get_directory(torrent_hash)
        multicall.d.is_multi_file(torrent_hash)
        (path, is_multi_file) = multicall()
        if is_multi_file :
            path = os.path.dirname(os.path.normpath(path))
        return path

    def defaultDataPrefix(self) :
        return self._server.get_directory()

    ###

    @classmethod
    def customKeys(cls) :
        return ("1", "2", "3", "4", "5")

    @clientlib.hashOrTorrent
    @_catchUnknownTorrentFault
    def setCustoms(self, torrent_hash, customs_dict) :
        assert len(customs_dict) != 0, "Empty customs list"
        multicall = xmlrpc.client.MultiCall(self._server)
        for (key, value) in customs_dict.items() :
            getattr(multicall.d, "set_custom" + key)(torrent_hash, value)
        multicall()

    @clientlib.hashOrTorrent
    @_catchUnknownTorrentFault
    def customs(self, torrent_hash, keys_list) :
        assert len(keys_list) != 0, "Empty customs list"
        keys_list = list(set(keys_list))
        multicall = xmlrpc.client.MultiCall(self._server)
        for key in keys_list :
            getattr(multicall.d, "get_custom" + key)(torrent_hash)
        results_list = list(multicall())
        return { keys_list[index] : results_list[index] for index in range(len(keys_list)) }

    ###

    @clientlib.hashOrTorrent
    @_catchUnknownTorrentFault
    def fullPath(self, torrent_hash) :
        return self._server.d.get_base_path(torrent_hash)

    @clientlib.hashOrTorrent
    @_catchUnknownTorrentFault
    def name(self, torrent_hash) :
        return self._server.d.get_name(torrent_hash)

    @clientlib.hashOrTorrent
    @_catchUnknownTorrentFault
    def isSingleFile(self, torrent_hash) :
        return not self._server.d.is_multi_file(torrent_hash)

    @clientlib.hashOrTorrent
    @_catchUnknownTorrentFault
    def files(self, torrent_hash, system_path_flag = False) :
        multicall = xmlrpc.client.MultiCall(self._server)
        multicall.d.get_base_path(torrent_hash)
        multicall.d.get_base_filename(torrent_hash)
        multicall.d.is_multi_file(torrent_hash)
        multicall.d.get_size_files(torrent_hash)
        multicall.f.get_size_bytes(torrent_hash, 0)
        (base_path, base_file_name, is_multi_file, count, first_file_size) = tuple(multicall())
        base = ( base_path if system_path_flag else base_file_name )

        if not is_multi_file :
            return { base : { "size" : first_file_size } }

        multicall = xmlrpc.client.MultiCall(self._server)
        for index in range(count) :
            multicall.f.get_path(torrent_hash, index)
            multicall.f.get_size_bytes(torrent_hash, index)
        files_list = list(multicall())
        files_list = list(zip(files_list[::2], files_list[1::2]))

        files_dict = clientlib.buildFiles(base, files_list)
        files_dict.update({ base : None })
        return files_dict

