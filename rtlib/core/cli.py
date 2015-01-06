import sys

from ulib.ui import cli

from colorama import Fore
from colorama import Style


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
