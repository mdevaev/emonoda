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


import sys
import os
import contextlib
import argparse

import pygments
import pygments.lexers.data
import pygments.formatters

from ..optconf import make_config
from ..optconf import Section
from ..optconf import Option

from ..optconf import build_raw_from_options
from ..optconf.dumper import make_config_dump
from ..optconf.loader import load_file as load_yaml_file
from ..optconf.converters import (
    as_string_or_none,
    as_string_list,
    as_key_value,
    as_path,
    as_paths_list,
    as_path_or_none,
    as_8int_or_none,
)

from ..plugins import get_client_class
from ..plugins import get_tracker_class
from ..plugins import get_confetti_class

from ..plugins.trackers import WithLogin as F_WithLogin
from ..plugins.trackers import WithCaptcha as F_WithCaptcha
from ..plugins.trackers import WithCheckTime as F_WithCheckTime
from ..plugins.clients import WithCustoms as C_WithCustoms

from .. import cli


# =====
def init():
    args_parser = argparse.ArgumentParser(add_help=False)
    args_parser.add_argument("-c", "--config", dest="config_file_path", default="~/.config/emonoda.yaml", metavar="<file>")
    args_parser.add_argument("-o", "--set-options", dest="set_options", default=[], nargs="+")
    args_parser.add_argument("-m", "--dump-config", dest="dump_config", action="store_true")
    (options, remaining) = args_parser.parse_known_args(sys.argv)

    options.config_file_path = os.path.expanduser(options.config_file_path)
    if os.path.exists(options.config_file_path):
        raw_config = load_yaml_file(options.config_file_path)
    else:
        raw_config = {}
    _merge_dicts(raw_config, build_raw_from_options(options.set_options))
    scheme = _get_config_scheme()
    config = make_config(raw_config, scheme)

    if config.core.client is not None:
        client_scheme = get_client_class(config.core.client).get_options()
        scheme["client"] = client_scheme

    for tracker_name in raw_config.get("trackers", []):
        tracker_scheme = get_tracker_class(tracker_name).get_options()
        scheme.setdefault("trackers", {})
        scheme["trackers"][tracker_name] = tracker_scheme

    for confetti_name in raw_config.get("confetti", []):
        confetti_scheme = get_confetti_class(confetti_name).get_options()
        scheme.setdefault("confetti", {})
        scheme["confetti"][confetti_name] = confetti_scheme

    config = make_config(raw_config, scheme)

    if options.dump_config:
        dump = make_config_dump(config)
        if sys.stdout.isatty():
            dump = pygments.highlight(
                dump,
                pygments.lexers.data.YamlLexer(),
                pygments.formatters.TerminalFormatter(bg="dark"),
            )
        print(dump)
        sys.exit(0)

    config.setdefault("client", Section())
    config.setdefault("trackers", Section())
    config.setdefault("confetti", Section())

    return (args_parser, remaining, config)


def _merge_dicts(dest, src, path=None):
    if path is None:
        path = []
    for key in src:
        if key in dest:
            if isinstance(dest[key], dict) and isinstance(src[key], dict):
                _merge_dicts(dest[key], src[key], list(path) + [str(key)])
                continue
        dest[key] = src[key]


# =====
@contextlib.contextmanager
def get_configured_log(config, quiet, output):
    log = cli.Log(config.core.use_colors, config.core.force_colors, quiet, output)
    try:
        yield log
    finally:
        log.finish()


def get_configured_client(config, required, with_customs, log):
    name = config.core.client
    if name is not None:
        log.info("Enabling the client {blue}%s{reset} ...", (name,), one_line=True)
        try:
            cls = get_client_class(name)
            if with_customs and C_WithCustoms not in cls.get_bases():
                raise RuntimeError("Your client does not support custom fields")
            client = cls(**config.client)
        except Exception as err:
            log.error("Can't init client {red}%s{reset}: {red}%s{reset}(%s)", (name, type(err).__name__, err))
            raise
        log.info("Client {blue}%s{reset} is {green}ready{reset}", (name,))
        return client
    elif required:
        raise RuntimeError("No configured client found")
    else:
        return None


def get_configured_trackers(config, captcha_decoder, only, exclude, log):
    to_init = set(config.trackers).difference(exclude)
    if len(only) != 0:
        to_init = to_init.intersection(only)

    if len(to_init) == 0:
        raise RuntimeError("No trackers to init")

    trackers = []
    for name in sorted(to_init):
        log.info("Enabling the tracker {blue}%s{reset} ...", (name,), one_line=True)

        cls = get_tracker_class(name)
        bases = cls.get_bases()
        kwargs = dict(config.trackers[name])
        if F_WithCaptcha in cls.get_bases():
            kwargs["captcha_decoder"] = captcha_decoder
        tracker = cls(**kwargs)

        try:
            log.info("Enabling the tracker {blue}%s{reset}: {yellow}testing{reset} ...", (name,), one_line=True)
            tracker.test()
            if F_WithLogin in bases:
                log.info("Enabling the tracker {blue}%s{reset}: {yellow}logging in{reset} ...", (name,), one_line=True)
                tracker.login()
            if F_WithCheckTime in bases:
                log.info("Enabling the tracker {blue}%s{reset}: {yellow}configuring timezone{reset} ...", (name,), one_line=True)
                tracker.init_tzinfo()
            log.info("Tracker {blue}%s{reset} is {green}ready{reset}", (name,))
        except Exception as err:
            log.error("Can't init tracker {red}%s{reset}: {red}%s{reset}(%s)", (name, type(err).__name__, err))
            if config.emupdate.fail_bad_tracker:
                raise
            continue

        trackers.append(tracker)

    return trackers


def get_configured_confetti(config, log):
    senders = []
    for name in sorted(config.confetti):
        log.info("Enabling the confetti {blue}%s{reset} ...", (name,), one_line=True)
        cls = get_confetti_class(name)
        try:
            senders.append(cls(**config.confetti[name]))
            log.info("Confetti {blue}%s{reset} is {green}ready{reset}", (name,))
        except Exception as err:
            log.error("Can't init confetti {red}%s{reset}: {red}%s{reset}(%s)", (name, type(err).__name__, err))
            raise
    return senders


# =====
def _get_config_scheme():
    return {
        "core": {
            "client":        Option(default=None, type=as_string_or_none, help="The name of plugin for torrent client"),
            "torrents_dir":  Option(default=".", type=as_path, help="Path to directory with torrent files"),
            "data_root_dir": Option(default="~/Downloads", type=as_path, help="Path to root directory with data of torrents"),
            "another_data_root_dirs": Option(default=[], type=as_paths_list, help="Paths to another data directories"),
            "use_colors":    Option(default=True, help="Enable colored output"),
            "force_colors":  Option(default=False, help="Always use the coloring"),
        },

        "emupdate": {
            "name_filter":   Option(default="*.torrent", help="Update only filtered torrent files"),
            "backup_dir":    Option(default=None, type=as_path_or_none, help="Backup old torrent files after update here"),
            "backup_suffix": Option(default=".%Y.%m.%d-%H:%M:%S.bak", help="Append this suffix to backuped file"),
            "save_customs":  Option(default=[], type=as_string_list, help="Save client custom fields after update if supports"),
            "set_customs":   Option(default={}, type=as_key_value, help="Set client custom fileds after update if supports"),
            "show_unknown":  Option(default=False, help="Show the torrents with unknown tracker in the log"),
            "show_passed":   Option(default=False, help="Show the torrents without changes"),
            "show_diff":     Option(default=True, help="Show diff between old and updated torrent files"),
            "fail_bad_tracker": Option(default=True, help="Fail on trackers with invalid configuration"),
        },

        "emfile": {
            "show_customs": Option(default=[], type=as_string_list, help="Show custom fields from client"),
        },

        "emload": {
            "mkdir_mode":  Option(default=None, type=as_8int_or_none, help="Permission for new directories"),
            "set_customs": Option(default={}, type=as_key_value, help="Set client custom fileds after update if supports")
        },

        "emfind": {
            "cache_file":  Option(default="~/.cache/emfind.json", type=as_path, help="Torrents cache"),
            "name_filter": Option(default="*.torrent", help="Cache only filtered torrent files"),
        },
    }
