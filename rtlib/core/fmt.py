import math
import datetime
import traceback


# =====
_UNITS = tuple(zip(
    ("bytes", "kB", "MB", "GB", "TB", "PB"),
    (0,       0,    1,    2,    2,    2),
))


# =====
def format_size(size):
    if size > 1:
        exponent = min(int(math.log(size, 1024)), len(_UNITS) - 1)
        quotient = float(size) / 1024 ** exponent
        (unit, decimals) = _UNITS[exponent]
        result = ("{:.%sf} {}" % (decimals)).format(quotient, unit)
    elif size == 0:
        result = "0 bytes"
    elif size == 1:
        result = "1 byte"
    else:
        ValueError("size must be >= 0")
    return result


def format_progress(value, limit):
    return (("%%%dd/" % (len(str(limit)))) + "%d") % (value, limit)


def format_now(text):
    return datetime.datetime.now().strftime(text)


def format_traceback(prefix):
    lines = []
    for row in traceback.format_exc().strip().split("\n") :
        lines.append(prefix + row)
    return "\n".join(lines)


def format_torrents_diff(diff, prefix):
    lines = []
    for (sign, color, items) in (
        ("+", "green",  diff.added),
        ("-", "red",    diff.removed),
        ("~", "cyan",   diff.modified),
        ("?", "yellow", diff.type_modified),
    ):
        for item in sorted(items):
            lines.append("%s{%s}%s{reset} %s" % (prefix, color, sign, item))
    return "\n".join(lines)


# =====
def make_fan():
    fan = 0
    while True:
        if fan < 3:
            fan += 1
        else:
            fan = 0
        yield "/-\\|"[fan]
