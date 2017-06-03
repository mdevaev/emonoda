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

import yaml

from ...optconf import Option
from ...optconf.converters import as_string_or_none
from ...optconf.converters import as_path_or_none

from . import BaseConfetti
from . import templated


# =====
def get_uid(user):
    return pwd.getpwnam(user)[2]


def get_gid(group):
    return grp.getgrnam(group)[2]


def get_user_groups(user):
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
    PLUGIN_NAME = "atom"

    def __init__(self,  # pylint: disable=super-init-not-called,too-many-arguments
                 history_path, path, url, user, group, template, html, **kwargs):
        self._init_bases(**kwargs)

        self._history_path = history_path
        self._path = path
        self._url = url
        self._user = (get_uid(user) if user else -1)
        self._group = (get_gid(group) if group else -1)
        if self._group != -1:
            if self._group not in get_user_groups(getpass.getuser()):
                raise UserError(
                    "I wouldn't be able to edit {path} with current user if I chown it for"
                    " uid {uid} and gid {gid}".format(path=path, uid=self._user, gid=self._group),
                )
        self._template_path = template
        self._html = html

    @classmethod
    def get_options(cls):
        return cls._get_merged_options({
            "history_path": Option(default="emonoda_history.yaml", type=as_path_or_none, help="Destination email address"),
            "path":         Option(default="atom.xml", type=as_path_or_none, help="Destination email address"),
            "url":          Option(default="http://localhost/", type=as_string_or_none, help="Feed server url"),
            "user":         Option(default=None, type=as_string_or_none, help="Server user"),
            "group":        Option(default=None, type=as_string_or_none, help="Server user group"),
            "template":     Option(default=None, type=as_path_or_none, help="Mako template file name"),
            "html":         Option(default=True, help="HTML or plaintext feed")
        })

    # ===

    def send_results(self, source, results):
        results_set = []
        try:
            with open(self._history_path) as history_file:
                results_set = yaml.load(history_file)
        except Exception:
            traceback.print_exc()
        results["ctime"] = time.time()
        results_set.insert(0, results)
        results_set = results_set[:20]
        built_in = (self._template_path is None)
        with open(self._path, "w") as atom_file:
            atom_file.write(templated(
                name=("atom.{ctype}.{source}.mako" if built_in else self._template_path).format(
                    ctype=("html" if self._html else "plain"),
                    source=source,
                    results_set=results_set,
                ),
                built_in=built_in,
                source=source,
                results_set=results_set,
                settings=dict(url=self._url)
            ))
        os.chmod(self._path, 0o664)
        os.chown(self._path, self._user, self._group)
        with open(self._history_path, "w") as history_file:
            history_file.write(yaml.dump(results_set))
        del results["ctime"]
