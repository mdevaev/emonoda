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
import re
import hashlib
import base64
import urllib.parse
import itertools

from typing import List
from typing import Dict
from typing import FrozenSet
from typing import NamedTuple
from typing import Optional
from typing import Union
from typing import Any

import chardet

from .thirdparty import bencoder  # type: ignore


# =====
class TorrentEntryAttrs(NamedTuple):
    is_dir: bool
    size: int

    @staticmethod
    def file(size: int) -> "TorrentEntryAttrs":
        return TorrentEntryAttrs(is_dir=False, size=size)

    @staticmethod
    def dir() -> "TorrentEntryAttrs":
        return TorrentEntryAttrs(is_dir=True, size=0)


class TorrentsDiff(NamedTuple):
    added: FrozenSet[str] = frozenset()
    removed: FrozenSet[str] = frozenset()
    modified: FrozenSet[str] = frozenset()
    type_modified: FrozenSet[str] = frozenset()

    def __bool__(self) -> bool:
        return bool(self.added or self.removed or self.modified or self.type_modified)


class Torrent:
    def __init__(self, data: Optional[bytes]=None, path: Optional[str]=None) -> None:
        # https://wiki.theory.org/index.php/BitTorrentSpecification

        self.__path = path
        self.__data: Optional[bytes] = None
        self.__bencode: Optional[Dict] = None
        self.__hash: str = ""
        self.__scrape_hash: str = ""

        if data is not None:
            self.load_from_data(data, path)
        elif path is not None:
            self.load_from_file(path)

    def load_from_file(self, path: str) -> "Torrent":
        with open(path, "rb") as torrent_file:
            return self.load_from_data(torrent_file.read(), path)

    def load_from_data(self, data: bytes, path: Optional[str]=None) -> "Torrent":
        self.__bencode = decode_torrent_data(data)
        self.__path = path
        self.__data = data
        self.__hash = ""
        self.__scrape_hash = ""
        return self

    # =====

    def get_path(self) -> str:
        assert self.__path, self
        return self.__path

    def get_data(self) -> bytes:
        assert self.__data, self
        return self.__data

    # =====

    def get_name(self, surrogate_escape: bool=False) -> str:
        assert self.__bencode, (self, self.__bencode)
        return self.__decode(self.__bencode[b"info"][b"name"], surrogate_escape)

    def get_comment(self) -> str:
        assert self.__bencode, (self, self.__bencode)
        return self.__decode(self.__bencode.get(b"comment", "").strip())

    def get_creation_date(self) -> int:
        assert self.__bencode, (self, self.__bencode)
        return self.__bencode.get(b"creation date", 0)

    def get_created_by(self) -> Optional[str]:
        assert self.__bencode, (self, self.__bencode)
        created_by = self.__bencode.get(b"created by")
        return (self.__decode(created_by) if created_by is not None else None)

    def get_announce(self) -> Optional[str]:
        assert self.__bencode, (self, self.__bencode)
        announce = self.__bencode.get(b"announce")
        return (self.__decode(announce) if announce is not None else None)

    def get_announce_list(self) -> List[List[str]]:
        assert self.__bencode, (self, self.__bencode)
        return [
            list(map(self.__decode, announce_list))
            for announce_list in self.__bencode.get(b"announce-list", [])
        ]

    def is_private(self) -> bool:
        assert self.__bencode, (self, self.__bencode)
        return bool(self.__bencode[b"info"].get(b"private", 0))

    # =====

    def get_hash(self) -> str:
        if not self.__hash:
            assert self.__bencode, (self, self.__bencode)
            self.__hash = hashlib.sha1(bencoder.bencode(self.__bencode[b"info"])).hexdigest().lower()
        return self.__hash

    def get_scrape_hash(self) -> str:
        if not self.__scrape_hash:
            torrent_hash = self.get_hash()
            for index in range(0, len(torrent_hash), 2):
                self.__scrape_hash += "%{}".format(torrent_hash[index:index + 2])
        return self.__scrape_hash

    def make_magnet(self, extras: Optional[List[str]]=None) -> str:
        extras = (extras or [])

        assert self.__bencode, (self, self.__bencode)
        # http://stackoverflow.com/questions/12479570/given-a-torrent-file-how-do-i-generate-a-magnet-link-in-python
        info_sha1 = hashlib.sha1(bencoder.bencode(self.__bencode[b"info"]))
        info_digest = info_sha1.digest()
        b32_hash = base64.b32encode(info_digest)

        magnet = "magnet:?xt={}".format(urllib.parse.quote_plus("urn:btih:{}".format(b32_hash)))
        if "name" in extras:
            magnet += "&dn={}".format(urllib.parse.quote_plus(self.get_name()))
        if "trackers" in extras:
            announces = self.get_announce_list()
            announce = self.get_announce()
            if announce:
                announces.insert(0, [announce])
            for announce in set(itertools.chain.from_iterable(announces)):
                magnet += "&tr={}".format(urllib.parse.quote_plus(announce))
        if "size" in extras:
            magnet += "&xl={}".format(self.get_size())
        return magnet

    # =====

    def get_size(self) -> int:
        assert self.__bencode, (self, self.__bencode)
        if self.is_single_file():
            return self.__bencode[b"info"][b"length"]
        else:
            size = 0
            for fstruct in self.__bencode[b"info"][b"files"]:
                size += fstruct[b"length"]
            return size

    def is_single_file(self) -> bool:
        assert self.__bencode, (self, self.__bencode)
        return (b"files" not in self.__bencode[b"info"])

    def get_files(self, prefix: str="") -> Dict[str, TorrentEntryAttrs]:
        assert self.__bencode, (self, self.__bencode)
        base = os.path.join(prefix, self.get_name())
        if self.is_single_file():
            return {base: TorrentEntryAttrs.file(self.__bencode[b"info"][b"length"])}
        else:
            files = {base: TorrentEntryAttrs.dir()}
            for fstruct in self.__bencode[b"info"][b"files"]:
                name = None
                for index in range(len(fstruct[b"path"])):
                    name = os.path.join(base, os.path.sep.join(map(self.__decode, fstruct[b"path"][0:index + 1])))
                    files[name] = TorrentEntryAttrs.dir()
                assert name is not None
                files[name] = TorrentEntryAttrs.file(fstruct[b"length"])
            return files

    # =====

    def __decode(self, value: Any, surrogate_escape: bool=False) -> str:  # pylint: disable=inconsistent-return-statements
        assert self.__bencode, (self, self.__bencode)
        if isinstance(value, bytes):
            if surrogate_escape:
                # https://www.python.org/dev/peps/pep-0383
                return value.decode("ascii", "surrogateescape")

            for encoding in [self.__bencode.get(b"encoding", b"utf-8").decode(), "cp1251"]:
                try:
                    return value.decode(encoding)
                except UnicodeDecodeError:
                    pass

            encoding = chardet.detect(value)["encoding"]
            assert encoding is not None, "Can't determine encoding for bytes string: '{}'".format(repr(value))
            return value.decode(encoding)
        else:
            return value


def is_valid_torrent_data(data: bytes) -> bool:
    try:
        decode_torrent_data(data)
        return True
    except ValueError:
        return False


def decode_torrent_data(data: bytes) -> Dict:
    try:
        result = bencoder.bdecode(data)
    except bencoder.BTFailure as err:
        raise ValueError from err
    if not isinstance(result, dict):
        raise ValueError("Toplevel structure must be a dict")
    return result


def is_torrent_hash(text: str) -> bool:
    return (re.match(r"[\da-fA-F]{40}", text) is not None)


def get_torrents_difference(
    old: Union[Torrent, Dict[str, TorrentEntryAttrs]],
    new: Union[Torrent, Dict[str, TorrentEntryAttrs]],
) -> TorrentsDiff:

    old_files = (old.get_files() if isinstance(old, Torrent) else old)
    files = (new.get_files() if isinstance(new, Torrent) else new)

    modified = set()
    type_modified = set()

    for path in set(old_files).intersection(set(files)):
        if old_files[path].is_dir != files[path].is_dir:
            type_modified.add(path)
        elif old_files[path].size != files[path].size:
            modified.add(path)

    return TorrentsDiff(
        added=frozenset(files).difference(frozenset(old_files)),
        removed=frozenset(old_files).difference(frozenset(files)),
        modified=frozenset(modified),
        type_modified=frozenset(type_modified),
    )
