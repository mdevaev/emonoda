import os
import re
import fnmatch
import hashlib
import base64
import urllib.parse
import collections
import itertools

from bcoding import (
    bdecode as decode_data,
    bencode as encode_struct,
)


# =====
ALL_MAGNET_FIELDS = ("dn", "tr", "xl")


# =====
def load_torrent_from_path(path):
    try:
        return Torrent(path=path)
    except TypeError:
        return None


def load_from_dir(dir_path, name_filter="*.torrent", as_abs=False, load_torrent=load_torrent_from_path):
    torrents = {}
    for name in os.listdir(dir_path):
        if fnmatch.fnmatch(name, name_filter):
            path = os.path.join(dir_path, name)
            if as_abs:
                path = os.path.abspath(path)
            torrents[name] = load_torrent(path)
    return torrents


def is_valid_data(data):
    try:
        return isinstance(decode_data(data), dict)  # Must be a True
    except TypeError:
        return False


def is_hash(text):
    return (re.match(r"[\da-fA-F]{40}", text) is not None)


def get_indexed(path, prefix="", name_filter="*.torrent"):
    files = {}
    for torrent in filter(None, load_from_dir(path, name_filter).values()):
        for path in torrent.get_files():
            full_path = os.path.join(prefix, path)
            files.setdefault(full_path, set())
            files[full_path].add(torrent)
    return files


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

    return Diff(
        added=set(new).difference(set(old)),
        removed=set(old).difference(set(new)),
        modified=modified,
        type_modified=type_modified,
    )


# =====
Diff = collections.namedtuple("Diff", ("added", "removed", "modified", "type_modified"))


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

    def get_name(self):
        return self._bencode["info"]["name"]

    def get_comment(self):
        return self._bencode.get("comment")

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
        if "dn" in extras:
            magnet += "&dn={}".format(urllib.parse.quote_plus(self.get_name()))
        if "tr" in extras:
            announces = tuple(filter(None, [self.get_announce()] + self.get_announce_list()))
            for announce in set(itertools.chain.from_iterable(announces)):
                magnet += "&tr={}".format(urllib.parse.quote_plus(announce))
        if "xl" in extras:
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
                    name = os.path.join(base, os.path.sep.join(fstruct["path"][0:index + 1]))
                    files[name] = None
                assert name is not None
                files[name] = make_file_attrs(fstruct)
            return files
