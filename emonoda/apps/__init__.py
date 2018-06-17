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

from typing import TextIO
from typing import Tuple
from typing import List
from typing import Dict
from typing import Sequence
from typing import Callable
from typing import Generator
from typing import Optional
from typing import Type
from typing import Any

import pygments
import pygments.lexers.data
import pygments.formatters

from ..optconf import make_config
from ..optconf import Section
from ..optconf import Option

from ..optconf import build_raw_from_options
from ..optconf.dumper import make_config_dump
from ..optconf.loader import load_file as load_yaml_file
from ..optconf.converters import as_string_list
from ..optconf.converters import as_key_value
from ..optconf.converters import as_path
from ..optconf.converters import as_paths_list
from ..optconf.converters import as_path_or_empty
from ..optconf.converters import as_8int

from ..plugins.clients import get_client_class
from ..plugins.trackers import get_tracker_class
from ..plugins.confetti import get_confetti_class

from ..plugins.trackers import BaseTracker
from ..plugins.trackers import WithLogin as T_WithLogin
from ..plugins.trackers import WithCaptcha as T_WithCaptcha
from ..plugins.trackers import WithCheckTime as T_WithCheckTime
from ..plugins.clients import BaseClient
from ..plugins.clients import WithCustoms as C_WithCustoms
from ..plugins.confetti import BaseConfetti

from ..cli import Log


# =====
class StoreTrueOrderedAction(argparse.Action):
    def __init__(
        self,
        option_strings: Sequence[str],
        dest: str,
        default: bool=False,
        required: bool=False,
        help: Optional[str]=None,  # pylint: disable=redefined-builtin
    ) -> None:

        super().__init__(
            option_strings=option_strings,
            dest=dest,
            nargs=0,
            const=True,
            default=default,
            required=required,
            help=help,
        )

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: Any,
        option_string: Any=None,
    ) -> None:

        # XXX: vulture hacks
        _ = parser
        _ = option_string  # type: ignore
        del _

        if not hasattr(namespace, "ordered_flags"):
            setattr(namespace, "ordered_flags", [])
        namespace.ordered_flags.append((self.dest, self.const))


def init() -> Tuple[argparse.ArgumentParser, List[str], Section]:
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

    if config.core.client:
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


def wrap_main(method: Callable[..., None]) -> Callable[..., None]:
    def wrap() -> None:
        try:
            method()
        except (SystemExit, KeyboardInterrupt):
            sys.exit(1)
    return wrap


def validate_client_customs(client: C_WithCustoms, customs: List[str]) -> None:
    invalid = sorted(set(customs).difference(client.get_custom_keys()))
    if invalid:
        raise RuntimeError("Invalid custom keys: {}".format(", ".join(invalid)))


def _merge_dicts(dest: Dict, src: Dict) -> None:
    for key in src:
        if key in dest:
            if isinstance(dest[key], dict) and isinstance(src[key], dict):
                _merge_dicts(dest[key], src[key])
                continue
        dest[key] = src[key]


# =====
@contextlib.contextmanager
def get_configured_log(config: Section, quiet: bool, output: TextIO) -> Generator[Log, None, None]:
    log = Log(config.core.use_colors, config.core.force_colors, quiet, output)
    try:
        yield log
    finally:
        log.finish()


def get_configured_client(config: Section, required: bool, with_customs: bool, log: Log) -> Optional[BaseClient]:
    name = config.core.client
    if name:
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


def get_configured_trackers(
    config: Section,
    captcha_decoder: Callable[[str], str],
    only: List[str],
    exclude: List[str],
    required_bases: List[Type[BaseTracker]],
    fail_bad_tracker: bool,
    log: Log,
) -> List[BaseTracker]:

    to_init = set(config.trackers).difference(exclude)
    if len(only) != 0:
        to_init = to_init.intersection(only)

    for name in list(to_init):
        if not set(required_bases).issubset(get_tracker_class(name).get_bases()):
            to_init.remove(name)

    if len(to_init) == 0:
        raise RuntimeError("No trackers to init")

    trackers = []
    for name in sorted(to_init):
        log.info("Enabling the tracker {blue}%s{reset} ...", (name,), one_line=True)

        cls = get_tracker_class(name)
        bases = cls.get_bases()
        kwargs = dict(config.trackers[name])
        if T_WithCaptcha in cls.get_bases():
            kwargs["captcha_decoder"] = captcha_decoder
        tracker = cls(**kwargs)

        try:
            log.info("Enabling the tracker {blue}%s{reset}: {yellow}testing{reset} ...", (name,), one_line=True)
            tracker.test()
            if T_WithLogin in bases:
                log.info("Enabling the tracker {blue}%s{reset}: {yellow}logging in{reset} ...", (name,), one_line=True)
                tracker.login()  # type: ignore
            if T_WithCheckTime in bases:
                log.info("Enabling the tracker {blue}%s{reset}: {yellow}configuring timezone{reset} ...", (name,), one_line=True)
                tracker.init_tzinfo()  # type: ignore
            log.info("Tracker {blue}%s{reset} is {green}ready{reset}", (name,))
        except Exception as err:
            log.error("Can't init tracker {red}%s{reset}: {red}%s{reset}(%s)", (name, type(err).__name__, err))
            if fail_bad_tracker:
                raise
            continue

        trackers.append(tracker)

    return trackers


def get_configured_confetti(
    config: Section,
    only: List[str],
    exclude: List[str],
    log: Log,
) -> List[BaseConfetti]:

    to_init = set(config.confetti).difference(exclude)
    if len(only) != 0:
        to_init = to_init.intersection(only)

    senders: List[BaseConfetti] = []
    for name in sorted(to_init):
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
def _get_config_scheme() -> Dict:
    return {
        "core": {
            "client":        Option(default="", help="The name of plugin for torrent client"),
            "torrents_dir":  Option(default=".", type=as_path, help="Path to directory with torrent files"),
            "data_root_dir": Option(default="~/Downloads", type=as_path_or_empty, help="Path to root directory with data of torrents"),
            "another_data_root_dirs": Option(default=[], type=as_paths_list, help="Paths to another data directories"),
            "use_colors":    Option(default=True, help="Enable colored output"),
            "force_colors":  Option(default=False, help="Always use the coloring"),
        },

        "emupdate": {
            "name_filter":   Option(default="*.torrent", help="Update only filtered torrent files"),
            "backup_dir":    Option(default="", type=as_path_or_empty, help="Backup old torrent files after update here"),
            "backup_suffix": Option(default=".%Y.%m.%d-%H:%M:%S.bak", help="Append this suffix to backuped file"),
            "save_customs":  Option(default=[], type=as_string_list, help="Save client custom fields after update if supports"),
            "set_customs":   Option(default={}, type=as_key_value, help="Set client custom fileds after update if supports"),
            "show_unknown":  Option(default=False, help="Show the torrents with unknown tracker in the log"),
            "show_passed":   Option(default=False, help="Show the torrents without changes"),
            "show_diff":     Option(default=True, help="Show diff between old and updated torrent files"),
            "fail_bad_tracker": Option(default=True, help="Fail on trackers with invalid configuration"),
        },

        "emstat": {
            "min_seeders":      Option(default=5, help="Minimal seeders to green color"),
            "fail_bad_tracker": Option(default=True, help="Fail on trackers with invalid configuration"),
        },

        "emfile": {
            "show_customs": Option(default=[], type=as_string_list, help="Show custom fields from client"),
        },

        "emload": {
            "mkdir_mode":  Option(default=-1, type=as_8int, help="Permission for new directories"),
            "set_customs": Option(default={}, type=as_key_value, help="Set client custom fileds after update if supports")
        },

        "emfind": {
            "cache_file":  Option(default="~/.cache/emfind.pk", type=as_path, help="Torrents cache"),
            "name_filter": Option(default="*.torrent", help="Cache only filtered torrent files"),
            "ignore_orphans": Option(default=[], type=as_paths_list, help="Ignore these paths on the final analyse"),
        },
    }
