"""
    Emonoda -- A set of tools to organize and manage your torrents
    Copyright (C) 2015  Devaev Maxim <mdevaev@gmail.com>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


import importlib
import functools
import os

from typing import Tuple
from typing import List
from typing import Dict
from typing import Optional
from typing import Type
from typing import Any

from ..optconf import Option


# =====
class BasePlugin:
    PLUGIN_NAMES: List[str] = []

    def __init__(self, **_: Any) -> None:
        pass

    @classmethod
    def get_options(cls) -> Dict[str, Option]:
        return {}

    @classmethod
    def get_bases(cls) -> "List[Type[BasePlugin]]":
        return cls.__get_bases(cls.__mro__)

    def _init_bases(self, **kwargs: Any) -> None:
        assert self.PLUGIN_NAMES
        for parent in self.__get_bases(self.__class__.__mro__):
            parent.__init__(self, **kwargs)  # type: ignore

    @classmethod
    def _get_merged_options(cls, params: Optional[Dict[str, Option]]=None) -> Dict[str, Option]:
        merged: Dict[str, Option] = {}
        for parent in cls.__get_bases(cls.__mro__):
            merged.update(parent.get_options())
        merged.update(params or {})
        return merged

    @staticmethod
    def __get_bases(mro: Tuple[Type, ...]) -> "List[Type[BasePlugin]]":
        return [
            cls for cls in mro
            if issubclass(cls, BasePlugin)
        ][1:]


@functools.lru_cache()
def get_classes(sub: str) -> Dict[str, Type[BasePlugin]]:
    classes: Dict[str, Type[BasePlugin]] = {}  # noqa: E701
    sub_path = os.path.join(os.path.dirname(__file__), sub)
    for file_name in os.listdir(sub_path):
        if not file_name.startswith("__") and file_name.endswith(".py"):
            module_name = file_name[:-3]
            module = importlib.import_module("emonoda.plugins.{}.{}".format(sub, module_name))
            plugin_class = getattr(module, "Plugin")
            for plugin_name in plugin_class.PLUGIN_NAMES:
                classes[plugin_name] = plugin_class
    return classes
