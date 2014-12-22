import sys
import inspect
from datetime import datetime

from colorama import Fore
from colorama import Style


# =====
RED    = Style.BRIGHT + Fore.RED
GREEN  = Style.BRIGHT + Fore.GREEN
YELLOW = Style.BRIGHT + Fore.YELLOW
CYAN   = Style.BRIGHT + Fore.CYAN


# =====
def has_extensions(cls, *exts):
    exts = set(exts)
    if not inspect.isclass(cls):
        cls = cls.__class__
    return (set(inspect.getmro(cls)).intersection(exts) == exts)


def get_date_by_format(fmt):
    return datetime.now().strftime(fmt)


def get_colored(color, text, force_colors, output=sys.stdout):
    if (output.isatty() or force_colors):
        return "".join([color] + [text] + [Fore.RESET])
    return text


def make_colored(use_colors, force_colors):
    if use_colors:
        return (lambda color, text: get_colored(color, text, force_colors))
    else:
        return (lambda color, text: text)


def print_torrents_diff(diff, prefix="", use_colors=True, force_colors=False, output=sys.stdout):
    for (sign, color, items) in (
        ("+", GREEN,  diff.added),
        ("-", RED,    diff.removed),
        ("~", CYAN,   diff.modified),
        ("?", YELLOW, diff.type_modified),
    ):
        for item in sorted(items):
            if use_colors:
                sign = get_colored(color, sign, force_colors=force_colors, output=output)
            print("{}{} {}".format(prefix, sign, item), file=output)


def make_fan():
    fan = 0
    while True:
        if fan < 3:
            fan += 1
        else:
            fan = 0
        yield "/-\\|"[fan]
