import sys
import os
import contextlib
import argparse

from ..optconf import make_config
from ..optconf import Section
from ..optconf import Option

from ..optconf.dumper import make_config_dump
from ..optconf.loaders.yaml import load_file as load_yaml_file

from ..core import cli

from ..plugins import get_client_class
from ..plugins import get_fetcher_class

from ..plugins.fetchers import WithLogin as F_WithLogin
from ..plugins.fetchers import WithCaptcha as F_WithCaptcha


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


@contextlib.contextmanager
def get_configured_log(config, quiet, output):
    log = cli.Log(config.core.use_colors, config.core.force_colors, quiet, output)
    try:
        yield log
    finally:
        log.finish()


def get_configured_client(config, log):
    if config.core.client is not None:
        log.print("# Enabling the client {blue}%s{reset} ..." % (config.core.client), one_line=True)
        client = get_client_class(config.core.client)(**config.client)
        log.print("# Client {blue}%s{reset} is {green}ready{reset}" % (config.core.client))
        return client
    else:
        return None


def get_configured_fetchers(config, captcha_decoder, only, exclude, log):
    to_init = set(config.fetchers).difference(exclude)
    if len(only) != 0:
        to_init.intersection(only)

    if len(to_init) == 0:
        raise RuntimeError("No fetchers to init")

    fetchers = []
    for fetcher_name in sorted(to_init):
        log.print("# Enabling the fetcher {blue}%s{reset} ..." % (fetcher_name), one_line=True)

        fetcher_class = get_fetcher_class(fetcher_name)
        fetcher_kwargs = dict(config.fetchers[fetcher_name])
        if F_WithCaptcha in fetcher_class.get_bases():
            fetcher_kwargs["captcha_decoder"] = captcha_decoder
        fetcher = fetcher_class(**fetcher_kwargs)

        try:
            fetcher.test_site()
            if F_WithLogin in fetcher_class.get_bases():
                fetcher.login()
            log.print("# Fetcher {blue}%s{reset} is {green}ready{reset}" % (fetcher_name))
        except Exception as err:
            log.print("# Init error: {red}%s{reset}: {red}%s{reset}(%s)" % (fetcher_name, type(err).__name__, err))
            raise

        fetchers.append(fetcher)

    return fetchers


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
            "show_unknown":      Option(default=False, help="Show the torrents with unknown tracker in the log"),
            "show_passed":       Option(default=False, help="Show the torrents without changes"),
            "show_diff":         Option(default=True, help="Show diff between old and updated torrent files"),
            "save_customs":      Option(default=[], type=(lambda items: list(map(str, items))),
                                        help="Save client custom fields after update (if supports)"),
            "set_customs":       Option(default=[], type=(lambda items: list(map(str, items))),
                                        help="Set client custom fileds after update (if supports)"),
        },
    }
