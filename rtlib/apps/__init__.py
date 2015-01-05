import sys
import os
import argparse

from ..core.clientlib import get_client_class
from ..core.fetcherlib import get_fetcher_class

from ..optconf import (
    Section,
    Option,
    make_config,
)
from ..optconf.dumper import make_config_dump
from ..optconf.loaders.yaml import load_file as load_yaml_file


# =====
def init():
    args_parser = argparse.ArgumentParser(add_help=False)
    args_parser.add_argument("-c", "--config", dest="config_file_path", default="~/.config/rt.yaml", metavar="<file>")
    args_parser.add_argument("-m", "--dump-config", dest="dump_config", action="store_true")
    (options, remaining) = args_parser.parse_known_args(sys.argv)

    options.config_file_path = os.path.expanduser(options.config_file_path)
    if os.path.exists(options.config_file_path):
        raw_config = load_yaml_file(options.config_file_path)
    else:
        raw_config = {}
    scheme = _get_config_scheme()
    config = make_config(raw_config, scheme)

    if config.core.client is not None:
        client_scheme = get_client_class(config.core.client).get_options()
        scheme["client"] = client_scheme
        config = make_config(raw_config, scheme)

    for fetcher_name in raw_config.get("fetchers", []):
        fetcher_scheme = get_fetcher_class(fetcher_name).get_options()
        scheme.setdefault("fetchers", {})
        scheme["fetchers"][fetcher_name] = fetcher_scheme
    config = make_config(raw_config, scheme)

    if options.dump_config:
        print(make_config_dump(config, split_by=((), ("fetchers",))))
        sys.exit(0)

    config.setdefault("client", Section())
    config.setdefault("fetchers", Section())

    return (args_parser, remaining, config)


def get_configured_client(config):
    if config.core.client is not None:
        return get_client_class(config.core.client)(**config.client)
    else:
        return None


# =====
def _get_config_scheme():
    return {
        "core": {
            "client":       Option(default=None, type=str, help="The name of plugin for torrent client"),
            "torrents_dir": Option(default=".", type=str, help="Path to directory with torrent files"),
            "use_colors":   Option(default=True, help="Enable colored output"),
            "force_colors": Option(default=False, help="Always use the coloring"),
        },

        "rtfetch": {
            "backup_dir":        Option(default=None, type=str, help="Backup old torrent files after update here"),
            "backup_suffix":     Option(default=".%Y.%m.%d-%H:%M:%S.bak", help="Append this suffix to backuped file"),
            "pass_failed_login": Option(default=False, help="Don't crash when login error accured"),
            "skip_unknown":      Option(default=True, help="Don't show the torrents with unknown tracker in the log"),
            "show_passed":       Option(default=False, help="Show the torrents without changes"),
            "show_diff":         Option(default=True, help="Show diff between old and updated torrent files"),
            "save_customs":      Option(default=[], type=(lambda items: list(map(str, items))),
                                        help="Save client custom fields after update (if supports)"),
            "set_customs":       Option(default=[], type=(lambda items: list(map(str, items))),
                                        help="Set client custom fileds after update (if supports)"),
        },
    }
