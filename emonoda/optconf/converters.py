import os


# =====
def as_string_or_none(value):
    if value is None:
        return None
    return str(value)


def as_string_list(values):
    return list(map(str, values))


def as_path(value):
    return os.path.abspath(os.path.expanduser(value))


def as_path_or_none(value):
    if value is None:
        return None
    return as_path(value)


def as_8int_or_none(value):
    if value is None:
        return None
    return int(str(value), 8)
