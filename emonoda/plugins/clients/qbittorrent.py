"""
    Emonoda -- A set of tools to organize and manage your torrents
    Copyright (C) 2018  Devaev Maxim <mdevaev@gmail.com>

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
import urllib.parse
import urllib.error
import http.cookiejar
import json

from typing import List
from typing import Dict
from typing import Optional
from typing import Any

from ...optconf import Option
from ...optconf import SecretOption

from ...tfile import TorrentEntryAttrs
from ...tfile import Torrent

from ... import web

from . import BaseClient
from . import NoSuchTorrentError
from . import hash_or_torrent
from . import check_torrent_accessible
from . import build_files


# =====
class Plugin(BaseClient):
    # API description: https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-Documentation

    PLUGIN_NAMES = ["qbittorrent"]

    def __init__(  # pylint:disable=super-init-not-called
        self,
        url: str,
        user: str,
        passwd: str,
        timeout: float,
        **kwargs: Any,
    ) -> None:

        self._init_bases(**kwargs)

        self.__url = url
        self.__timeout = timeout

        self.__opener = web.build_opener(
            cookie_jar=(http.cookiejar.CookieJar() if user else None)
        )
        if user:
            self.__post(
                path="/login",
                payload={
                    "username": user,
                    "password": passwd,
                },
            )

    @classmethod
    def get_options(cls) -> Dict[str, Option]:
        return cls._get_merged_options({
            "url":     Option(default="http://localhost:8080", help="WebUI URL"),
            "user":    Option(default="", help="WebUI Login"),
            "passwd":  SecretOption(default="", help="WebUI Password"),
            "timeout": Option(default=10.0, help="Network timeout"),
        })

    # =====

    @hash_or_torrent
    def remove_torrent(self, torrent_hash: str) -> None:
        self.__get_torrent_props(torrent_hash)  # XXX: raise NoSuchTorrentError if torrent does not exist
        self.__post(
            path="/command/delete",
            payload={"hashes": torrent_hash},
        )

    @check_torrent_accessible
    def load_torrent(self, torrent: Torrent, prefix: str) -> None:
        self.__post(
            path="/command/upload",
            payload={
                "save_path": prefix,
                "savepath": prefix,
            },
            files={
                "torrents": web.MultipartFile(
                    name=os.path.basename(torrent.get_path()),
                    mimetype="application/x-bittorrent",
                    data=torrent.get_data(),
                ),
            },
        )

    @hash_or_torrent
    def has_torrent(self, torrent_hash: str) -> bool:
        return bool(json.loads(self.__get("/query/torrents?hashes={}".format(torrent_hash))))

    def get_hashes(self) -> List[str]:
        return [
            item["hash"].lower()
            for item in json.loads(self.__get("/query/torrents"))
        ]

    @hash_or_torrent
    def get_data_prefix(self, torrent_hash: str) -> str:
        return self.__get_torrent_props(torrent_hash)["save_path"]

    def get_data_prefix_default(self) -> str:
        return json.loads(self.__get("/query/preferences"))["save_path"]

    # =====

    @hash_or_torrent
    def get_full_path(self, torrent_hash: str) -> str:
        props = self.__get_torrent_props(torrent_hash)
        return os.path.join(props["save_path"], props["name"])

    @hash_or_torrent
    def get_file_name(self, torrent_hash: str) -> str:
        return self.__get_torrent_props(torrent_hash)["name"]

    @hash_or_torrent
    def get_files(self, torrent_hash: str) -> Dict[str, TorrentEntryAttrs]:
        try:
            return build_files("", [
                (item["name"], item["size"])
                for item in json.loads(self.__get("/query/propertiesFiles/{}".format(torrent_hash)))
            ])
        except urllib.error.HTTPError as err:
            if err.code == 404:
                raise NoSuchTorrentError("Unknown torrent hash")
            raise

    # =====

    def __get_torrent_props(self, torrent_hash: str) -> Dict[str, Any]:
        result = json.loads(self.__get("/query/torrents?hashes={}".format(torrent_hash)))
        assert len(result) >= 0, (torrent_hash, result)
        if len(result) == 0:
            raise NoSuchTorrentError("Unknown torrent hash")
        return result[0]

    def __get(self, path: str) -> str:
        return self.__read_handle(path).decode("utf-8")

    def __post(
        self,
        path: str,
        payload: Dict[str, str],
        files: Optional[Dict[str, web.MultipartFile]]=None,
    ) -> None:

        page = self.__read_handle(
            path=path,
            payload=payload,
            files=files,
        ).decode("utf-8")
        if page.lower().startswith("fails"):
            raise RuntimeError("{} error: {}".format(path, page.strip()))

    def __read_handle(
        self,
        path: str,
        payload: Optional[Dict[str, str]]=None,
        files: Optional[Dict[str, web.MultipartFile]]=None,
    ) -> bytes:

        data = headers = None
        if files:
            (data, headers) = web.encode_multipart((payload or {}), files)
        elif payload:
            data = urllib.parse.urlencode(payload).encode("utf-8")
        return web.read_url(
            opener=self.__opener,
            url=urllib.parse.urljoin(self.__url, path),
            data=data,
            headers=headers,
            timeout=self.__timeout,
            retries=3,
            retries_sleep=5.0,
            retry_codes=[500, 502],
        )
