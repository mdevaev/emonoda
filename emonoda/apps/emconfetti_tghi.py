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


import sys
import argparse

from . import init
from . import wrap_main
from . import get_configured_log
from . import get_configured_confetti


# ===== Main =====
@wrap_main
def main() -> None:
    (parent_parser, argv, config) = init()
    args_parser = argparse.ArgumentParser(
        prog="emconfetti-tghi",
        description="Telegram-bot helper",
        parents=[parent_parser],
    )
    args_parser.add_argument("-n", "--limit", default=10, type=int)
    options = args_parser.parse_args(argv[1:])

    with get_configured_log(config, False, sys.stdout) as log_stdout:
        with get_configured_log(config, False, sys.stdout) as log_stderr:
            confetti = get_configured_confetti(
                config=config,
                only=["telegram"],
                exclude=[],
                log=log_stderr,
            )
            if len(confetti) == 0:
                raise RuntimeError("No configured telegram plugin")
            assert hasattr(confetti[0], "get_last_chats"), confetti[0]
            for (user, chat_id) in confetti[0].get_last_chats(options.limit):  # type: ignore
                log_stdout.print("- Chat with user '{yellow}%s{reset}': %s", (user, chat_id))


if __name__ == "__main__":
    main()  # Do the thing!
