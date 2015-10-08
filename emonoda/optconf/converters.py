import os


# =====
def as_string_or_none(value):
    if value is None:
        return None
    return str(value)


def as_string_list(values):
    if isinstance(values, str):
        values = [values]
    return list(map(str, values))


def as_key_value(values):
    if isinstance(values, dict):
        return values
    return dict(
        tuple(map(str.strip, (item.split("=", 1) + [""])[:2]))
        for item in as_string_list(values)
        if len(item.split("=", 1)[0].strip()) != 0
    )


def as_path(value):
    return os.path.abspath(os.path.expanduser(value))


def as_paths_list(values):
    if isinstance(values, str):
        values = [values]
    return list(map(as_path, values))


def as_path_or_none(value):
    if value is None:
        return None
    return as_path(value)


def as_8int_or_none(value):
    if value is None:
        return None
    return int(str(value), 8)
