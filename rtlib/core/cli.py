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

    def print(self, text="", use_colors=None, force_colors=None, output=None, one_line=False):
        use_colors = self._select(use_colors, self._use_colors)
        force_colors = self._select(force_colors, self._force_colors)
        output = self._select(output, self._output)

        if use_colors and (output.isatty() or force_colors):
            colors = _COLORS
        else:
            colors = dict.fromkeys(list(_COLORS), "")

        text = text.format(**colors)
        if not self._quiet:
            _inner_print(text, one_line, output)

    def _select(self, first, second):
        return (first if first is not None else second)


# =====
_last_text = ""


def _inner_print(text, one_line, output):
    global _last_text  # pylint: disable=global-statement
    if one_line:
        to_print = " " * len(_last_text) + "\r" + text + "\r"
        _last_text = text
    else:
        if len(_last_text) != 0:
            to_print = " " * len(_last_text) + "\r" + text + "\n"
        else:
            to_print = text + "\n"
        _last_text = ""
    output.write(to_print)
    output.flush()
