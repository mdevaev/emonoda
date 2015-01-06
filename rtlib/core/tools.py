import sys
import operator

from datetime import datetime

from ulib.ui import cli

from colorama import Fore
from colorama import Style

from . import tfile


# =====
def get_date_by_format(fmt):
    return datetime.now().strftime(fmt)


def make_fan():
    fan = 0
    while True:
        if fan < 3:
            fan += 1
        else:
            fan = 0
        yield "/-\\|"[fan]


# =====
class Log:
    _colors = {
        "red":     Style.BRIGHT + Fore.RED,
        "green":   Style.BRIGHT + Fore.GREEN,
        "yellow":  Style.BRIGHT + Fore.YELLOW,
        "cyan":    Style.BRIGHT + Fore.CYAN,
        "magenta": Style.BRIGHT + Fore.MAGENTA,
        "blue":    Style.BRIGHT + Fore.BLUE,
        "reset":   Fore.RESET,
    }

    def __init__(self, use_colors=True, force_colors=False, output=sys.stdout):
        self._use_colors = use_colors
        self._force_colors = force_colors
        self._output = output

    def print(self, text="", use_colors=None, force_colors=None, output=None, one_line=False):
        use_colors = self._select(use_colors, self._use_colors)
        force_colors = self._select(force_colors, self._force_colors)
        output = self._select(output, self._output)

        if use_colors and (output.isatty() or force_colors):
            colors = self._colors
        else:
            colors = dict.fromkeys(list(self._colors), "")

        text = text.format(**colors)
        handler = (cli.one_line if one_line else cli.new_line)
        handler(text, output=output)

    def _select(self, first, second):
        return (first if first is not None else second)


# =====
def print_torrents_diff(diff, prefix, log):
    for (sign, color, items) in (
        ("+", "green",  diff.added),
        ("-", "red",    diff.removed),
        ("~", "cyan",   diff.modified),
        ("?", "yellow", diff.type_modified),
    ):
        for item in sorted(items):
            log.print("%s{%s}%s{reset} %s" % (prefix, color, sign, item))


def load_torrents_from_dir(dir_path, name_filter, log):
    fan = make_fan()

    def load_torrent(path):
        log.print("# Caching {cyan}%s/{yellow}%s {magenta}%s{reset}" % (
                  dir_path, name_filter, next(fan)), one_line=True)
        return tfile.load_torrent_from_path(path)

    torrents = list(sorted(
        tfile.load_from_dir(dir_path, name_filter, as_abs=True, load_torrent=load_torrent).items(),
        key=operator.itemgetter(0),
    ))

    log.print("# Cached {magenta}%d{reset} torrents from {cyan}%s/{yellow}%s{reset}" % (
              len(torrents), dir_path, name_filter))
    return torrents
