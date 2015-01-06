import sys
import os
import shutil
import argparse

from ulib import fmt
from ulib.ui import cli

from ..core import tfile
from ..core import tools

from ..plugins import get_bases
from ..plugins import get_fetcher_class

from ..plugins.clients import WithCustoms as C_WithCustoms

from ..plugins.fetchers import FetcherError
from ..plugins.fetchers import WithLogin as F_WithLogin
from ..plugins.fetchers import WithCaptcha as F_WithCaptcha

from . import init
from . import get_configured_client


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
            if C_WithCustoms in get_bases(client) and len(to_save_customs) != 0:
                old_customs = client.get_customs(torrent, to_save_customs)
            prefix = client.get_data_prefix(torrent)
            client.remove_torrent(torrent)

        with open(torrent.get_path(), "wb") as torrent_file:
            torrent_file.write(new_data)
        torrent.load_from_data(new_data, torrent.get_path())

        if client is not None:
            client.load_torrent(torrent, prefix)
            if C_WithCustoms in get_bases(client):
                if len(to_save_customs) != 0:
                    client.set_customs(torrent, old_customs)
                if len(to_set_customs) != 0:
                    client.set_customs(torrent, {
                        key: tools.get_date_by_format(value)
                        for (key, value) in to_set_customs.items()
                    })

    return diff


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
    noop,
    log_stdout,
    log_stderr,
):
    invalid_count = 0
    not_in_client_count = 0
    unknown_count = 0
    passed_count = 0
    updated_count = 0
    error_count = 0

    torrents = tools.load_torrents_from_dir(
        dir_path=torrents_dir_path,
        name_filter=name_filter,
        log=log_stderr,
    )
    hashes = (client.get_hashes() if client is not None else [])

    log_stdout.print()

    for (count, (torrent_file_name, torrent)) in enumerate(torrents):
        progress = fmt.format_progress(count + 1, len(torrents))
        format_fail = (lambda error, color="red", sign="!": "[{%s}%s{reset}] %s {blue}%s {cyan}%s{reset}" % (
                       color, sign, progress, error, torrent_file_name))  # pylint: disable=cell-var-from-loop

        if torrent is None:
            log_stdout.print(format_fail("INVALID_TIRRENT"))
            invalid_count += 1
            continue

        if client is not None and torrent.get_hash() not in hashes:
            log_stdout.print(format_fail("NOT_IN_CLIENT"))
            not_in_client_count += 1
            continue

        fetcher = select_fetcher(torrent, fetchers)
        if fetcher is None:
            unknown_count += 1
            if not skip_unknown:
                log_stdout.print(format_fail("UNKNOWN", "yellow", " "))
            continue

        format_status = (lambda color, sign: "[{%s}%s{reset}] %s {blue}%s {cyan}%s{reset} -- %s" % (
                         color, sign, progress, fetcher.get_name(),  # pylint: disable=cell-var-from-loop
                         torrent_file_name, (torrent.get_comment() or "")))  # pylint: disable=cell-var-from-loop

        try:
            if F_WithLogin in get_bases(fetcher) and not fetcher.is_logged_in():
                log_stdout.print(format_status("yellow", "?"))
                error_count += 1
                continue

            if not fetcher.is_torrent_changed(torrent):
                log_stdout.print(format_status("blue", " "), one_line=(not show_passed))
                passed_count += 1
                continue

            if not noop and backup_dir_path is not None:
                backup_torrent(torrent, backup_dir_path, backup_suffix)
            diff = update_torrent(client, fetcher, torrent, to_save_customs, to_set_customs, noop)

            log_stdout.print(format_status("green", "+"))
            if show_diff:
                tools.print_torrents_diff(diff, "\t", log_stdout)

            updated_count += 1

        except FetcherError as err:
            log_stdout.print(format_status("red", "-") +
                             " :: {red}%s({reset}%s{red}){reset}" % (type(err).__name__, err))
            error_count += 1

        except Exception as err:
            log_stdout.print(format_status("red", "-"))
            cli.print_traceback("\t")
            error_count += 1

    if (
        (client is not None and not_in_client_count)
        or (not skip_unknown and unknown_count)
        or (show_passed and passed_count)
        or invalid_count
        or updated_count
        or error_count
    ):
        log_stdout.print()

    log_stderr.print("# " + ("-" * 10))
    log_stderr.print("# Invalid:       {}".format(invalid_count))
    if client is not None:
        log_stderr.print("# Not in client: {}".format(not_in_client_count))
    log_stderr.print("# Unknown:       {}".format(unknown_count))
    log_stderr.print("# Passed:        {}".format(passed_count))
    log_stderr.print("# Updated:       {}".format(updated_count))
    log_stderr.print("# Errors:        {}".format(error_count))


def read_captcha(url):
    print("# Enter the captcha from [ {} ] ?> ".format(url), output=sys.stderr)
    return input()


def init_fetchers(fetchers_config, only_fetchers, exclude_fetchers, pass_failed_login, log):
    to_init = set(fetchers_config).difference(exclude_fetchers)
    if len(only_fetchers) != 0:
        to_init.intersection(only_fetchers)

    fetchers = []
    for fetcher_name in sorted(to_init):
        log.print("# Enabling the fetcher {blue}%s{reset} ..." % (fetcher_name), one_line=True)

        fetcher_class = get_fetcher_class(fetcher_name)

        fetcher_kwargs = dict(fetchers_config[fetcher_name])
        if F_WithCaptcha in get_bases(fetcher_class):
            fetcher_kwargs["decode_captcha"] = read_captcha

        fetcher = fetcher_class(**fetcher_kwargs)

        try:
            fetcher.test_site()
            if F_WithLogin in get_bases(fetcher_class):
                fetcher.login()
            log.print("# Fetcher {blue}%s{reset} is {green}ready{reset}" % (fetcher_name))
        except Exception as err:
            log.print("# Init error: {red}%s{reset}: {red}%s{reset}(%s)" % (fetcher_name, type(err).__name__, err))
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

    log_stdout = tools.Log(config.core.use_colors, config.core.force_colors, sys.stdout)
    log_stderr = tools.Log(config.core.use_colors, config.core.force_colors, sys.stderr)

    client = get_configured_client(config)

    fetchers = init_fetchers(
        fetchers_config=config.fetchers,
        only_fetchers=options.only_fetchers,
        exclude_fetchers=options.exclude_fetchers,
        pass_failed_login=config.rtfetch.pass_failed_login,
        log=log_stderr,
    )

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
        noop=options.noop,
        log_stdout=log_stdout,
        log_stderr=log_stderr,
    )


if __name__ == "__main__":
    main()
