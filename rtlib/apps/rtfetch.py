import sys
import os
import shutil
import operator
import argparse

from ulib import fmt
from ulib.ui import cli

from ..core import tfile
from ..core import tools

from ..core.fetcher import (
    FetcherError,
    WithLogin as F_WithLogin,
    WithCaptcha as F_WithCaptcha,
    get_fetcher_class,
)

from ..core.client import (
    WithCustoms as C_WithCustoms,
    get_client_class,
)

from . import init


# =====
def backup_torrent(torrent, backup_dir_path, backup_suffix):
    backup_suffix = tools.get_date_by_format(backup_suffix)
    backup_file_path = os.path.join(backup_dir_path, os.path.basename(torrent.get_path()) + backup_suffix)
    shutil.copyfile(torrent.get_path(), backup_file_path)


def update_torrent(client, fetcher, torrent, to_save_customs, to_set_customs, noop):
    new_data = fetcher.fetch_new_data(torrent)
    diff = tfile.get_difference(torrent, tfile.Torrent(data=new_data))

    if not noop:
        if client is not None:
            if tools.has_extensions(client, C_WithCustoms) and len(to_save_customs) != 0:
                old_customs = client.get_customs(torrent, to_save_customs)
            prefix = client.get_data_prefix(torrent)
            client.remove_torrent(torrent)

        with open(torrent.get_path(), "wb") as torrent_file:
            torrent_file.write(new_data)
        torrent.load_from_data(new_data, torrent.get_path())

        if client is not None:
            client.load_torrent(torrent, prefix)
            if tools.has_extensions(client, C_WithCustoms):
                if len(to_save_customs) != 0:
                    client.set_customs(torrent, old_customs)
                if len(to_set_customs) != 0:
                    client.set_customs(torrent, {
                        key: tools.get_date_by_format(value)
                        for (key, value) in to_set_customs.items()
                    })

    return diff


def get_torrents(dir_path, name_filter):
    fan = tools.make_fan()

    def load_torrent(path):
        cli.one_line("# Caching {}/{} ... [{}]".format(dir_path, name_filter, next(fan)), output=sys.stderr)
        return tfile.load_torrent_from_path(path)

    torrents = list(sorted(
        tfile.load_from_dir(dir_path, name_filter, as_abs=True, load_torrent=load_torrent).items(),
        key=operator.itemgetter(0),
    ))

    cli.new_line("# Cached {} torrents from {}/{}".format(len(torrents), dir_path, name_filter), output=sys.stderr)
    return torrents


def read_captcha(url):
    print("# Enter the captcha from [ {} ] ?> ".format(url), output=sys.stderr)
    return input()


def select_fetcher(torrent, fetchers):
    for fetcher in fetchers:
        if fetcher.is_matched_for(torrent):
            return fetcher
    return None


def update(  # pylint: disable=too-many-arguments,too-many-locals,too-many-branches,too-many-statements
    client,
    fetchers,
    torrents_dir_path,
    name_filter,
    backup_dir_path,
    backup_suffix,
    to_save_customs,
    to_set_customs,
    skip_unknown,
    show_passed,
    show_diff,
    use_colors,
    force_colors,
    noop,
):
    invalid_count = 0
    not_in_client_count = 0
    unknown_count = 0
    passed_count = 0
    updated_count = 0
    error_count = 0

    torrents = get_torrents(torrents_dir_path, name_filter)
    hashes = (client.get_hashes() if client is not None else [])

    get_colored = tools.make_colored(use_colors, force_colors)
    for (count, (torrent_file_name, torrent)) in enumerate(torrents):
        status_line = "[{{sign}}] {progress} {{fetcher}} {torrent}".format(
            progress=fmt.format_progress(count + 1, len(torrents)),
            torrent=torrent_file_name,
        )
        format_fail = (lambda error, color=tools.RED, sign="!": status_line.format(  # pylint: disable=cell-var-from-loop
            sign=get_colored(color, sign),
            fetcher=get_colored(color, error),
        ))

        if torrent is None:
            cli.new_line(format_fail("INVALID_TIRRENT"))
            invalid_count += 1
            continue
        else:
            status_line += " --- {}".format(torrent.get_comment() or "")

        if client is not None and torrent.get_hash() not in hashes:
            cli.new_line(format_fail("NOT_IN_CLIENT"))
            not_in_client_count += 1
            continue

        fetcher = select_fetcher(torrent, fetchers)
        if fetcher is None:
            unknown_count += 1
            if not skip_unknown:
                cli.new_line(format_fail("UNKNOWN", tools.YELLOW, " "))
            continue

        format_status = (lambda color, sign: status_line.format(  # pylint: disable=cell-var-from-loop
            sign=(get_colored(color, sign) if color is not None else sign),
            fetcher=get_colored(color, fetcher.get_name()),  # pylint: disable=cell-var-from-loop
        ))

        try:
            if tools.has_extensions(fetcher, F_WithLogin) and not fetcher.is_logged_in():
                cli.new_line(format_status(tools.YELLOW, "?"))
                error_count += 1
                continue

            if not fetcher.is_torrent_changed(torrent):
                cli.one_line(format_status(tools.CYAN, " "), not show_passed)
                passed_count += 1
                continue

            if not noop and backup_dir_path is not None:
                backup_torrent(torrent, backup_dir_path, backup_suffix)
            diff = update_torrent(client, fetcher, torrent, to_save_customs, to_set_customs, noop)

            cli.new_line(format_status(tools.GREEN, "+"))
            if show_diff:
                tools.print_torrents_diff(diff, "\t", use_colors=use_colors, force_colors=force_colors)

            updated_count += 1

        except FetcherError as err:
            cli.new_line(format_status(tools.RED, "-") + " :: {}({})".format(type(err).__name__, err))
            error_count += 1

        except Exception as err:
            cli.new_line(format_status(tools.RED, "-"))
            cli.print_traceback("\t")
            error_count += 1

    cli.new_line("# " + ("-" * 10), output=sys.stderr)

    print("# Invalid:       {}".format(invalid_count))
    if client is not None:
        print("# Not in client: {}".format(not_in_client_count))
    print("# Unknown:       {}".format(unknown_count))
    print("# Passed:        {}".format(passed_count))
    print("# Updated:       {}".format(updated_count))
    print("# Errors:        {}".format(error_count))


def init_fetchers(fetchers_config, only_fetchers, exclude_fetchers, pass_failed_login, use_colors, force_colors):
    get_colored = tools.make_colored(use_colors, force_colors)
    to_init = set(fetchers_config).difference(exclude_fetchers)
    if len(only_fetchers) != 0:
        to_init.intersection(only_fetchers)

    fetchers = []
    for fetcher_name in sorted(to_init):
        cli.one_line("# Enabling the fetcher {} ...".format(get_colored(tools.CYAN, fetcher_name)), output=sys.stderr)

        fetcher_class = get_fetcher_class(fetcher_name)

        fetcher_kwargs = dict(fetchers_config[fetcher_name])
        if tools.has_extensions(fetcher_class, F_WithCaptcha):
            fetcher_kwargs["decode_captcha"] = read_captcha

        fetcher = fetcher_class(**fetcher_kwargs)

        try:
            fetcher.test_site()
            if tools.has_extensions(fetcher_class, F_WithLogin):
                fetcher.login()
            cli.new_line("# Fetcher {fetcher} is {ready}".format(
                fetcher=get_colored(tools.CYAN, fetcher_name),
                ready=get_colored(tools.GREEN, "ready"),
            ), output=sys.stderr)
        except Exception as err:
            cli.new_line("# Init error: {fetcher}: {exc}({err})".format(
                fetcher=get_colored(tools.RED, fetcher_name),
                exc=type(err).__name__,
                err=err,
            ), output=sys.stderr)
            if not pass_failed_login:
                raise

        fetchers.append(fetcher)
    return fetchers


# ===== Main =====
def main():
    (parent_parser, argv, config) = init()
    args_parser = argparse.ArgumentParser(
        prog="rtfetch",
        description="Update torrent files from popular trackers",
        parents=[parent_parser],
    )
    args_parser.add_argument("-f", "--name-filter", default="*.torrent", metavar="<wildcard_pattern>")
    args_parser.add_argument("-o", "--only-fetchers", default=[], nargs="+", metavar="<fetcher>")
    args_parser.add_argument("-x", "--exclude-fetchers", default=[], nargs="+", metavar="<fetcher>")
    args_parser.add_argument("--noop", action="store_true")
    options = args_parser.parse_args(argv[1:])

    if len(config.fetchers) == 0:
        print("# No available fetchers in config", file=sys.stderr)
        sys.exit(1)

    fetchers = init_fetchers(
        fetchers_config=config.fetchers,
        only_fetchers=options.only_fetchers,
        exclude_fetchers=options.exclude_fetchers,
        pass_failed_login=config.rtfetch.pass_failed_login,
        use_colors=config.core.use_colors,
        force_colors=config.core.force_colors,
    )

    if config.core.client is not None:
        client = get_client_class(config.core.client)(**config.client)
    else:
        client = None

    update(
        client=client,
        fetchers=fetchers,
        torrents_dir_path=config.core.torrents_dir,
        name_filter=options.name_filter,
        backup_dir_path=config.rtfetch.backup_dir,
        backup_suffix=config.rtfetch.backup_suffix,
        to_save_customs=config.rtfetch.save_customs,
        to_set_customs=config.rtfetch.set_customs,
        skip_unknown=config.rtfetch.skip_unknown,
        show_passed=config.rtfetch.show_passed,
        show_diff=config.rtfetch.show_diff,
        use_colors=config.core.use_colors,
        force_colors=config.core.force_colors,
        noop=options.noop,
    )


if __name__ == "__main__":
    main()
