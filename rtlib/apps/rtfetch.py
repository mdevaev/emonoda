import sys
import os
import shutil
import argparse

from ..plugins.clients import WithCustoms as C_WithCustoms
from ..plugins.fetchers import FetcherError
from ..plugins.fetchers import select_fetcher

from .. import tfile
from .. import fmt
from .. import helpers

from . import init
from . import get_configured_log
from . import get_configured_conveyor
from . import get_configured_client
from . import get_configured_fetchers


# =====
def backup_torrent(torrent, backup_dir_path, backup_suffix):
    backup_suffix = fmt.format_now(backup_suffix)
    backup_file_path = os.path.join(backup_dir_path, os.path.basename(torrent.get_path()) + backup_suffix)
    shutil.copyfile(torrent.get_path(), backup_file_path)


def update_torrent(client, fetcher, torrent, to_save_customs, to_set_customs, noop):
    new_data = fetcher.fetch_new_data(torrent)
    diff = tfile.get_difference(torrent, tfile.Torrent(data=new_data))

    if not noop:
        if client is not None:
            if C_WithCustoms in client.get_bases() and len(to_save_customs) != 0:
                old_customs = client.get_customs(torrent, to_save_customs)
            prefix = client.get_data_prefix(torrent)
            client.remove_torrent(torrent)

        with open(torrent.get_path(), "wb") as torrent_file:
            torrent_file.write(new_data)
        torrent.load_from_data(new_data, torrent.get_path())

        if client is not None:
            client.load_torrent(torrent, prefix)
            if C_WithCustoms in client.get_bases():
                if len(to_save_customs) != 0:
                    client.set_customs(torrent, old_customs)
                if len(to_set_customs) != 0:
                    client.set_customs(torrent, {
                        key: fmt.format_now(value)
                        for (key, value) in to_set_customs.items()
                    })

    return diff


def update(  # pylint: disable=too-many-arguments,too-many-locals
    conveyor,
    client,
    fetchers,
    backup_dir_path,
    backup_suffix,
    to_save_customs,
    to_set_customs,
    noop,
    log_stdout,
    log_stderr,
):
    hashes = (client.get_hashes() if client is not None else [])

#    log_stdout.print()

    for torrent in conveyor.get_torrents():
        if torrent is None:
            conveyor.mark_invalid()
            continue

        if client is not None and torrent.get_hash() not in hashes:
            conveyor.mark_not_in_client()
            continue

        fetcher = select_fetcher(torrent, fetchers)
        if fetcher is None:
            conveyor.mark_unknown()
            continue

        conveyor.mark_in_progress(fetcher)

        try:
            if not fetcher.is_torrent_changed(torrent):
                conveyor.mark_passed(fetcher)
                continue

            if not noop and backup_dir_path is not None:
                backup_torrent(torrent, backup_dir_path, backup_suffix)
            diff = update_torrent(client, fetcher, torrent, to_save_customs, to_set_customs, noop)

            conveyor.mark_updated(fetcher, diff)

        except FetcherError as err:
            conveyor.mark_fetcher_error(fetcher, err)

        except Exception:
            conveyor.mark_common_error(fetcher)
            log_stdout.print(fmt.format_traceback("\t"))

#    if (
#        (client is not None and conveyor.not_in_client_count)
#        or (show_unknown and conveyor.unknown_count)
#        or (show_passed and conveyor.passed_count)
#        or conveyor.invalid_count
#        or conveyor.updated_count
#        or conveyor.error_count
#    ):
#        log_stdout.print()

    log_stderr.print("# " + ("-" * 10))
    log_stderr.print("# Invalid:       {}".format(conveyor.invalid_count))
    if client is not None:
        log_stderr.print("# Not in client: {}".format(conveyor.not_in_client_count))
    log_stderr.print("# Unknown:       {}".format(conveyor.unknown_count))
    log_stderr.print("# Passed:        {}".format(conveyor.passed_count))
    log_stderr.print("# Updated:       {}".format(conveyor.updated_count))
    log_stderr.print("# Errors:        {}".format(conveyor.error_count))


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

    with get_configured_log(config, False, sys.stdout) as log_stdout:
        with get_configured_log(config, False, sys.stderr) as log_stderr:

            conveyor = get_configured_conveyor(config, log_stdout, log_stderr)

            client = get_configured_client(config, log_stderr)

            fetchers = get_configured_fetchers(
                config=config,
                captcha_decoder=conveyor.read_captcha,
                only=options.only_fetchers,
                exclude=options.exclude_fetchers,
                log=log_stderr,
            )

            conveyor.set_torrents(helpers.load_torrents_from_dir(
                dir_path=config.core.torrents_dir,
                name_filter=options.name_filter,
                log=log_stderr,
            ))

            update(
                conveyor=conveyor,
                client=client,
                fetchers=fetchers,
                backup_dir_path=config.rtfetch.backup_dir,
                backup_suffix=config.rtfetch.backup_suffix,
                to_save_customs=config.rtfetch.save_customs,
                to_set_customs=config.rtfetch.set_customs,
                noop=options.noop,
                log_stdout=log_stdout,
                log_stderr=log_stderr,
            )


if __name__ == "__main__":
    main()  # Do the thing!
