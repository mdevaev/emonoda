import sys

from colorama import Fore
from colorama import Style


# =====
_COLORS = {
    "red":     Style.BRIGHT + Fore.RED,
    "green":   Style.BRIGHT + Fore.GREEN,
    "yellow":  Style.BRIGHT + Fore.YELLOW,
    "cyan":    Style.BRIGHT + Fore.CYAN,
    "magenta": Style.BRIGHT + Fore.MAGENTA,
    "blue":    Style.BRIGHT + Fore.BLUE,
    "reset":   Fore.RESET,
}


# =====
class Log:
    def __init__(self, use_colors=True, force_colors=False, quiet=False, output=sys.stdout):
        self._use_colors = use_colors
        self._force_colors = force_colors
        self._quiet = quiet
        self._output = output

    def print(self, text="", one_line=False):
        if self._use_colors and (self._output.isatty() or self._force_colors):
            colors = _COLORS
        else:
            colors = dict.fromkeys(list(_COLORS), "")

        text = text.format(**colors)
        if not self._quiet:
            _inner_print(text, one_line, self._output)

    def finish(self):
        _inner_finish(self._output)


# =====
_next_ctl = ""


def _inner_print(text, one_line, output):
    global _next_ctl  # pylint: disable=global-statement
    output.write(_next_ctl + text)
    output.flush()
    _next_ctl = ("\r" + " " * len(text) + "\r" if one_line else "\n")


def _inner_finish(output):
    global _next_ctl  # pylint: disable=global-statement
    if len(_next_ctl) != 0:
        output.write("\n")
        output.flush()
        _next_ctl = ""
