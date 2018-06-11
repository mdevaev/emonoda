import os

from typing import List
from typing import Dict
from typing import Sequence
from typing import Union
from typing import Any


# =====
def as_string_list(values: Union[str, Sequence]) -> List[str]:
    if isinstance(values, str):
        values = [values]
    return list(map(str, values))


def as_string_list_choices(values: Union[str, Sequence], choices: List[str]) -> List[str]:
    values = as_string_list(values)
    invalid = sorted(set(values).difference(choices))
    if invalid:
        raise ValueError("Incorrect values: %r" % (invalid))
    return values


def as_key_value(values: Union[str, Dict[str, Any]]) -> Dict[str, str]:
    if isinstance(values, dict):
        return values
    return dict(
        tuple(map(str.strip, (item.split("=", 1) + [""])[:2]))  # type: ignore
        for item in as_string_list(values)
        if len(item.split("=", 1)[0].strip()) != 0
    )


def as_path(value: str) -> str:
    return os.path.normpath(os.path.abspath(os.path.expanduser(value)))


def as_paths_list(values: Sequence[str]) -> List[str]:
    if isinstance(values, str):
        values = [values]
    return list(map(as_path, values))


def as_path_or_empty(value: str) -> str:
    if value:
        return as_path(value)
    return ""


def as_8int(value: int) -> int:
    return int(str(value), 8)
