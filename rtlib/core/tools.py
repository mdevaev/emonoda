import sys
import inspect
import operator
from datetime import datetime

from ulib.ui import cli

from colorama import Fore
from colorama import Style

from . import tfile


# =====
def has_extensions(cls, *exts):
    exts = set(exts)
    if not inspect.isclass(cls):
        cls = cls.__class__
    return (set(inspect.getmro(cls)).intersection(exts) == exts)


def get_date_by_format(fmt):
    return datetime.now().strftime(fmt)


def say(text, one_line=False, use_colors=True, force_colors=False, output=sys.stdout):
    colors = {
        "red":     Style.BRIGHT + Fore.RED,
        "green":   Style.BRIGHT + Fore.GREEN,
        "yellow":  Style.BRIGHT + Fore.YELLOW,
        "cyan":    Style.BRIGHT + Fore.CYAN,
        "magenta": Style.BRIGHT + Fore.MAGENTA,
        "blue":    Style.BRIGHT + Fore.BLUE,
        "reset":   Fore.RESET,
    }
    if not (use_colors and (output.isatty() or force_colors)):
        colors = dict.fromkeys(list(colors), "")
    text = text.format(**colors)
    handler = (cli.one_line if one_line else cli.new_line)
    handler(text, output=output)


def make_say(use_colors=True, force_colors=False, output=sys.stdout):
    return (lambda text, one_line=False: say(text, one_line, use_colors, force_colors, output))


def make_fan():
    fan = 0
    while True:
        if fan < 3:
            fan += 1
        else:
            fan = 0
        yield "/-\\|"[fan]


# =====
def print_torrents_diff(diff, prefix="", use_colors=True, force_colors=False, output=sys.stdout):
    for (sign, color, items) in (
        ("+", "green",  diff.added),
        ("-", "red",    diff.removed),
        ("~", "cyan",   diff.modified),
        ("?", "yellow", diff.type_modified),
    ):
        for item in sorted(items):
            say(
                text="%s{%s}%s{reset} %s" % (prefix, color, sign, item),
                use_colors=use_colors,
                force_colors=force_colors,
                output=output,
            )


def load_torrents_from_dir(dir_path, name_filter, use_colors=True, force_colors=False, output=sys.stderr):
    say = make_say(use_colors, force_colors, output)  # pylint: disable=redefined-outer-name
    fan = make_fan()

    def load_torrent(path):
        say("# Caching {cyan}%s/{yellow}%s {magenta}%s{reset}" % (dir_path, name_filter, next(fan)), one_line=True)
        return tfile.load_torrent_from_path(path)

    torrents = list(sorted(
        tfile.load_from_dir(dir_path, name_filter, as_abs=True, load_torrent=load_torrent).items(),
        key=operator.itemgetter(0),
    ))

    say("# Cached {magenta}%d{reset} torrents from {cyan}%s/{yellow}%s{reset}" % (len(torrents), dir_path, name_filter))
    return torrents
