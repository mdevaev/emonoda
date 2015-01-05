import os
import importlib

from . import tfile


# =====
class NoSuchTorrentError(Exception):
    pass


def get_client_class(name):
    module = importlib.import_module("rtlib.clients." + name)
    return getattr(module, "Client")


# =====
def build_files(prefix, flist):
    files = {}
    for (path, size) in flist:
        path_list = path.split(os.path.sep)
        name = None
        for index in range(len(path_list)):
            name = os.path.join(prefix, os.path.sep.join(path_list[0:index + 1]))
            files[name] = None
        assert name is not None
        files[name] = {"size": size}
    return files


def hash_or_torrent(method):
    def wrap(self, torrent, *args, **kwargs):
        torrent_hash = (torrent.get_hash() if isinstance(torrent, tfile.Torrent) else torrent)
        return method(self, torrent_hash, *args, **kwargs)
    return wrap


def check_torrent_accessible(method):
    def wrap(self, torrent, prefix=None):
        path = torrent.get_path()
        assert path is not None, "Required Torrent() with local file"
        open(path, "rb").close()  # Check accessible file
        if prefix is not None:
            os.listdir(prefix)  # Check accessible prefix
        return method(self, torrent, prefix)
    return wrap


# =====
class BaseClient:
    @classmethod
    def get_name(cls):
        raise NotImplementedError

    @classmethod
    def get_options(cls):
        return {}

    # ===

    @hash_or_torrent
    def remove_torrent(self, torrent_hash):
        raise NotImplementedError

    @check_torrent_accessible
    def load_torrent(self, torrent, prefix=None):
        raise NotImplementedError

    def get_hashes(self):
        raise NotImplementedError

    @hash_or_torrent
    def has_torrent(self, torrent_hash):
        raise NotImplementedError

    @hash_or_torrent
    def get_torrent_path(self, torrent_hash):
        raise NotImplementedError

    @hash_or_torrent
    def get_data_prefix(self, torrent_hash):
        raise NotImplementedError

    def get_data_prefix_default(self):
        raise NotImplementedError

    # ===

    @hash_or_torrent
    def get_full_path(self, torrent_hash):
        raise NotImplementedError

    @hash_or_torrent
    def get_file_name(self, torrent_hash):
        raise NotImplementedError

    @hash_or_torrent
    def is_single_file(self, torrent_hash):
        raise NotImplementedError

    @hash_or_torrent
    def get_files(self, torrent_hash, on_fs=False):
        raise NotImplementedError


class WithCustoms:
    @classmethod
    def get_custom_keys(cls):
        raise NotImplementedError

    @hash_or_torrent
    def set_customs(self, torrent_hash, customs):  # pylint: disable=unused-argument
        raise NotImplementedError

    @hash_or_torrent
    def get_customs(self, torrent_hash, keys):  # pylint: disable=unused-argument
        raise NotImplementedError
