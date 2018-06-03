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
from typing import Set
from typing import NamedTuple
from typing import Optional
from typing import Union
from typing import Any

import chardet

from .thirdparty.bcoding import bdecode as _inner_decode_data
from .thirdparty.bcoding import bencode as encode_struct


# =====
class _InnerTorrentEntryAttrs(NamedTuple):
    is_dir: bool
    size: int


class TorrentEntryAttrs(_InnerTorrentEntryAttrs):
    @staticmethod
    def new_file(size: int) -> "TorrentEntryAttrs":
        return TorrentEntryAttrs(is_dir=False, size=size)

    @staticmethod
    def new_dir() -> "TorrentEntryAttrs":
        return TorrentEntryAttrs(is_dir=True, size=0)


class _InnerTorrentsDiff(NamedTuple):
    added: Set[str]
    removed: Set[str]
    modified: Set[str]
    type_modified: Set[str]


class TorrentsDiff(_InnerTorrentsDiff):
    @staticmethod
    def new(
        added: Optional[Set[str]]=None,
        removed: Optional[Set[str]]=None,
        modified: Optional[Set[str]]=None,
        type_modified: Optional[Set[str]]=None,
    ) -> "TorrentsDiff":

        return TorrentsDiff(
            added=(added or set()),
            removed=(removed or set()),
            modified=(modified or set()),
            type_modified=(type_modified or set()),
        )


class Torrent:
    def __init__(self, data: Optional[bytes]=None, path: Optional[str]=None) -> None:
        # https://wiki.theory.org/index.php/BitTorrentSpecification

        self._path = path
        self._data: Optional[bytes] = None
        self._bencode: Optional[Dict] = None
        self._hash: str = ""
        self._scrape_hash: str = ""

        if data is not None:
            self.load_from_data(data, path)
        elif path is not None:
            self.load_from_file(path)

    def load_from_file(self, path: str) -> "Torrent":
        with open(path, "rb") as torrent_file:
            return self.load_from_data(torrent_file.read(), path)

    def load_from_data(self, data: bytes, path: Optional[str]=None) -> "Torrent":
        self._bencode = decode_torrent_data(data)
        self._path = path
        self._data = data
        self._hash = ""
        self._scrape_hash = ""
        return self

    # ===

    def get_path(self) -> str:
        assert self._path, self
        return self._path

    def get_data(self) -> bytes:
        assert self._data, self
        return self._data

    def get_bencode(self) -> Dict:
        assert self._bencode, self
        return self._bencode

    # ===

    def get_name(self, surrogate_escape: bool=False) -> str:
        assert self._bencode, (self, self._bencode)
        return self._decode(self._bencode["info"]["name"], surrogate_escape)

    def get_comment(self) -> str:
        assert self._bencode, (self, self._bencode)
        return self._decode(self._bencode.get("comment", "").strip())

    # def get_encoding(self) -> Optional[str]:
    #     assert self._bencode, (self, self._bencode)
    #     return self._bencode.get("encoding")

    def get_creation_date(self) -> int:
        assert self._bencode, (self, self._bencode)
        return self._bencode.get("creation date", 0)

    def get_created_by(self) -> Optional[str]:
        assert self._bencode, (self, self._bencode)
        return self._bencode.get("created by")

    def get_announce(self) -> Optional[str]:
        assert self._bencode, (self, self._bencode)
        return self._bencode.get("announce")

    def get_announce_list(self) -> List[str]:
        assert self._bencode, (self, self._bencode)
        return self._bencode.get("announce-list", [])

    def is_private(self) -> bool:
        assert self._bencode, (self, self._bencode)
        return bool(self._bencode["info"].get("private", 0))

    # ===

    def get_hash(self) -> str:
        if not self._hash:
            assert self._bencode, (self, self._bencode)
            self._hash = hashlib.sha1(encode_struct(self._bencode["info"])).hexdigest().lower()
        return self._hash

    def get_scrape_hash(self) -> str:
        if not self._scrape_hash:
            torrent_hash = self.get_hash()
            for index in range(0, len(torrent_hash), 2):
                self._scrape_hash += "%{}".format(torrent_hash[index:index + 2])
        return self._scrape_hash

    def make_magnet(self, extras: Optional[List[str]]=None) -> str:
        extras = (extras or [])

        assert self._bencode, (self, self._bencode)
        # http://stackoverflow.com/questions/12479570/given-a-torrent-file-how-do-i-generate-a-magnet-link-in-python
        info_sha1 = hashlib.sha1(encode_struct(self._bencode["info"]))
        info_digest = info_sha1.digest()
        b32_hash = base64.b32encode(info_digest)

        magnet = "magnet:?xt={}".format(urllib.parse.quote_plus("urn:btih:{}".format(b32_hash)))
        if "name" in extras:
            magnet += "&dn={}".format(urllib.parse.quote_plus(self.get_name()))
        if "trackers" in extras:
            announces = self.get_announce_list()
            announce = self.get_announce()
            if announce:
                announces.insert(0, announce)
            for announce in set(itertools.chain.from_iterable(announces)):
                magnet += "&tr={}".format(urllib.parse.quote_plus(announce))
        if "size" in extras:
            magnet += "&xl={}".format(self.get_size())
        return magnet

    # ===

    def get_size(self) -> int:
        assert self._bencode, (self, self._bencode)
        if self.is_single_file():
            return self._bencode["info"]["length"]
        else:
            size = 0
            for fstruct in self._bencode["info"]["files"]:
                size += fstruct["length"]
            return size

    def is_single_file(self) -> bool:
        assert self._bencode, (self, self._bencode)
        return ("files" not in self._bencode["info"])

    def get_files(self, prefix: str="") -> Dict[str, TorrentEntryAttrs]:
        assert self._bencode, (self, self._bencode)
        base = os.path.join(prefix, self.get_name())
        if self.is_single_file():
            return {base: TorrentEntryAttrs.new_file(self._bencode["info"]["length"])}
        else:
            files = {base: TorrentEntryAttrs.new_dir()}
            for fstruct in self._bencode["info"]["files"]:
                name = None
                for index in range(len(fstruct["path"])):
                    name = os.path.join(base, os.path.sep.join(map(self._decode, fstruct["path"][0:index + 1])))
                    files[name] = TorrentEntryAttrs.new_dir()
                assert name is not None
                files[name] = TorrentEntryAttrs.new_file(fstruct["length"])
            return files

    # ===

    def _decode(self, value: Any, surrogate_escape: bool=False) -> str:  # pylint: disable=inconsistent-return-statements
        assert self._bencode, (self, self._bencode)
        if isinstance(value, bytes):
            if surrogate_escape:
                # https://www.python.org/dev/peps/pep-0383
                return value.decode("ascii", "surrogateescape")

            for encoding in [self._bencode.get("encoding", "utf-8"), "cp1251"]:
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
    except (TypeError, ValueError):
        return False


def decode_torrent_data(data: bytes) -> Dict:
    result = _inner_decode_data(data)
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
    new_files = (new.get_files() if isinstance(new, Torrent) else new)

    modified = set()
    type_modified = set()

    for path in set(old_files).intersection(set(new_files)):
        if old_files[path].is_dir != new_files[path].is_dir:
            type_modified.add(path)
        elif old_files[path].size != new_files[path].size:
            modified.add(path)

    return TorrentsDiff(
        added=set(new_files).difference(set(old_files)),
        removed=set(old_files).difference(set(new_files)),
        modified=modified,
        type_modified=type_modified,
    )
