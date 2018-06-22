"""
    Emonoda -- A set of tools to organize and manage your torrents
    Copyright (C) 2015  Devaev Maxim <mdevaev@gmail.com>

    atom.py -- produce atom feed file of recent torrent updates
    Copyright (C) 2017  Pavel Pletenev <cpp.create@gmail.com>

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
import getpass
import pwd
import grp
import traceback
import time

from typing import List
from typing import Dict
from typing import Any

import yaml

from ...optconf import Option
from ...optconf.converters import as_path
from ...optconf.converters import as_path_or_empty

from . import ResultsType
from . import BaseConfetti
from . import templated


# =====
def get_uid(user: str) -> int:
    return pwd.getpwnam(user)[2]


def get_gid(group: str) -> int:
    return grp.getgrnam(group)[2]


def get_user_groups(user: str) -> List[int]:
    groups = [
        group.gr_name
        for group in grp.getgrall()
        if user in group.gr_mem
    ]
    gid = pwd.getpwnam(user).pw_gid
    groups.append(grp.getgrgid(gid).gr_name)
    return [grp.getgrnam(group).gr_gid for group in groups]


class UserError(Exception):
    pass


# =====
class Plugin(BaseConfetti):  # pylint: disable=too-many-instance-attributes
    PLUGIN_NAMES = ["atom"]

    def __init__(  # pylint: disable=super-init-not-called,too-many-arguments
        self,
        history_path: str,
        path: str,
        url: str,
        user: str,
        group: str,
        template: str,
        html: bool,
        **kwargs: Any,
    ) -> None:

        self._init_bases(**kwargs)

        self.__history_path = history_path
        self.__path = path
        self.__url = url
        self.__uid = (get_uid(user) if user else -1)
        self.__gid = (get_gid(group) if group else -1)
        if self.__gid > -1:
            if self.__gid not in get_user_groups(getpass.getuser()):
                raise UserError(
                    "I wouldn't be able to edit {path} with current user if I chown it for "
                    "uid={uid} and gid={gid}".format(path=path, uid=self.__uid, gid=self.__gid),
                )
        self.__template_path = template
        self.__html = html

    @classmethod
    def get_options(cls) -> Dict[str, Option]:
        return cls._get_merged_options({
            "history_path": Option(default="emonoda_history.yaml", type=as_path, help="History path"),
            "path":         Option(default="atom.xml", type=as_path, help="Atom path"),
            "url":          Option(default="http://localhost/", help="Feed server url"),
            "user":         Option(default="", help="Server user"),
            "group":        Option(default="", help="Server user group"),
            "template":     Option(default="", type=as_path_or_empty, help="Mako template file name"),
            "html":         Option(default=True, help="HTML or plaintext feed")
        })

    def send_results(self, source: str, results: ResultsType) -> None:
        if len(results["affected"]) != 0:
            results_set: List[ResultsType] = []
            try:
                with open(self.__history_path) as history_file:
                    results_set = yaml.load(history_file)
            except Exception:
                traceback.print_exc()
            results["ctime"] = time.time()  # type: ignore
            results_set.insert(0, results)
            results_set = results_set[:20]
            with open(self.__path, "w") as atom_file:
                atom_file.write(templated(
                    name=(self.__template_path if self.__template_path else "atom.{ctype}.{source}.mako").format(
                        ctype=("html" if self.__html else "plain"),
                        source=source,
                    ),
                    built_in=(not self.__template_path),
                    source=source,
                    results_set=results_set,
                    settings=dict(url=self.__url)
                ))
            os.chmod(self.__path, 0o664)
            os.chown(self.__path, self.__uid, self.__gid)
            with open(self.__history_path, "w") as history_file:
                history_file.write(yaml.dump(results_set))
            del results["ctime"]
