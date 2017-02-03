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

import chardet

from .thirdparty.bcoding import bdecode as _inner_decode_data
from .thirdparty.bcoding import bencode as encode_struct


# =====
def is_valid_data(data):
    try:
        decode_data(data)
        return True
    except (TypeError, ValueError):
        return False


def decode_data(data):
    result = _inner_decode_data(data)
    if not isinstance(result, dict):
        raise ValueError("Toplevel structure must be a dict")
    return result


def is_hash(text):
    return (re.match(r"[\da-fA-F]{40}", text) is not None)


def get_difference(old, new):
    assert isinstance(old, (Torrent, dict))
    assert isinstance(new, (Torrent, dict))
    old = (old.get_files() if isinstance(old, Torrent) else old)
    new = (new.get_files() if isinstance(new, Torrent) else new)

    modified = set()
    type_modified = set()
    for path in set(old).intersection(set(new)):
        old_attrs = old[path]
        new_attrs = new[path]

        real = len(tuple(filter(None, (new_attrs, old_attrs))))
        if real == 0:
            continue
        elif real == 1:
            type_modified.add(path)
            continue

        if old_attrs["size"] != new_attrs["size"]:
            modified.add(path)

    return {
        "added":         set(new).difference(set(old)),
        "removed":       set(old).difference(set(new)),
        "modified":      modified,
        "type_modified": type_modified,
    }


# =====
class Torrent:
    def __init__(self, data=None, path=None):
        # https://wiki.theory.org/BitTorrentSpecification

        self._path = path
        self._data = None
        self._bencode = None
        self._hash = None
        self._scrape_hash = None

        if data is not None:
            self.load_from_data(data, path)
        elif path is not None:
            self.load_from_file(path)

    def load_from_file(self, path):
        with open(path, "rb") as torrent_file:
            return self.load_from_data(torrent_file.read(), path)

    def load_from_data(self, data, path=None):
        self._bencode = decode_data(data)
        self._path = path
        self._data = data
        self._hash = None
        self._scrape_hash = None
        return self

    # ===

    def get_path(self):
        return self._path

    def get_data(self):
        return self._data

    def get_bencode(self):
        return self._bencode

    # ===

    def get_name(self, surrogate_escape=False):
        return self._decode(self._bencode["info"]["name"], surrogate_escape)

    def get_comment(self):
        return self._decode(self._bencode.get("comment"))

    def get_encoding(self):
        return self._bencode.get("encoding")

    def get_creation_date(self):
        return self._bencode.get("creation date")

    def get_created_by(self):
        return self._bencode.get("created by")

    def get_announce(self):
        return self._bencode.get("announce")

    def get_announce_list(self):
        return self._bencode.get("announce-list", [])

    def is_private(self):
        return bool(self._bencode["info"].get("private", 0))

    # ===

    def get_hash(self):
        if self._hash is None:
            self._hash = hashlib.sha1(encode_struct(self._bencode["info"])).hexdigest().lower()
        return self._hash

    def get_scrape_hash(self):
        if self._scrape_hash is None:
            scrape_hash = ""
            torrent_hash = self.get_hash()
            for index in range(0, len(torrent_hash), 2):
                scrape_hash += "%{}".format(torrent_hash[index:index + 2])
            self._scrape_hash = scrape_hash
        return self._scrape_hash

    def make_magnet(self, extras=()):
        # http://stackoverflow.com/questions/12479570/given-a-torrent-file-how-do-i-generate-a-magnet-link-in-python
        info_sha1 = hashlib.sha1(encode_struct(self._bencode["info"]))
        info_digest = info_sha1.digest()
        b32_hash = base64.b32encode(info_digest)

        magnet = "magnet:?xt={}".format(urllib.parse.quote_plus("urn:btih:{}".format(b32_hash)))
        if "name" in extras:
            magnet += "&dn={}".format(urllib.parse.quote_plus(self.get_name()))
        if "trackers" in extras:
            announces = tuple(filter(None, [self.get_announce()] + self.get_announce_list()))
            for announce in set(itertools.chain.from_iterable(announces)):
                magnet += "&tr={}".format(urllib.parse.quote_plus(announce))
        if "size" in extras:
            magnet += "&xl={}".format(self.get_size())
        return magnet

    # ===

    def get_size(self):
        if self.is_single_file():
            return self._bencode["info"]["length"]
        else:
            size = 0
            for fstruct in self._bencode["info"]["files"]:
                size += fstruct["length"]
            return size

    def is_single_file(self):
        return ("files" not in self._bencode["info"])

    def get_files(self, prefix=""):
        make_file_attrs = (lambda fstruct: {"size": fstruct["length"]})
        base = os.path.join(prefix, self.get_name())
        if self.is_single_file():
            return {base: make_file_attrs(self._bencode["info"])}
        else:
            files = {base: None}
            for fstruct in self._bencode["info"]["files"]:
                name = None
                for index in range(len(fstruct["path"])):
                    name = os.path.join(base, os.path.sep.join(map(self._decode, fstruct["path"][0:index + 1])))
                    files[name] = None
                assert name is not None
                files[name] = make_file_attrs(fstruct)
            return files

    # ===

    def _decode(self, value, surrogate_escape=False):
        if isinstance(value, bytes):
            if surrogate_escape:
                # https://www.python.org/dev/peps/pep-0383
                return value.decode("ascii", "surrogateescape")

            for encoding in (self._bencode.get("encoding", "utf-8"), "cp1251"):
                try:
                    return value.decode(encoding)
                except UnicodeDecodeError:
                    pass

            encoding = chardet.detect(value)["encoding"]
            assert encoding is not None, "Can't determine encoding for bytes string: '{}'".format(repr(value))
            return value.decode(encoding)
        else:
            return value
