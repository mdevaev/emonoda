import math
import datetime


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


def make_fan():
    fan = 0
    while True:
        if fan < 3:
            fan += 1
        else:
            fan = 0
        yield "/-\\|"[fan]
