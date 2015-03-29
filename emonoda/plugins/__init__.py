"""
    Emonoda -- The set of tools to organize and manage your torrents
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


# =====
def get_conveyor_class(name):
    return _get_classes()["conveyors"][name]


def get_client_class(name):
    return _get_classes()["clients"][name]


def get_fetcher_class(name):
    return _get_classes()["fetchers"][name]


@functools.lru_cache()
def _get_classes():
    classes = {}
    for sub in ("conveyors", "clients", "fetchers"):
        classes.setdefault(sub, {})
        sub_path = os.path.join(os.path.dirname(__file__), sub)
        for file_name in os.listdir(sub_path):
            if not file_name.startswith("__") and file_name.endswith(".py"):
                module_name = file_name[:-3]
                module = importlib.import_module("emonoda.plugins.{}.{}".format(sub, module_name))
                plugin_class = getattr(module, "Plugin")
                classes[sub][plugin_class.get_name()] = plugin_class
    return classes


# =====
class BasePlugin:
    @classmethod
    def get_name(cls):
        raise NotImplementedError

    @classmethod
    def get_options(cls):
        return {}

    @classmethod
    def get_bases(cls):
        return cls.__bases__

    # ===

    def _init_bases(self, **kwargs):
        for parent in self.__class__.__bases__:
            parent.__init__(self, **kwargs)

    @classmethod
    def _get_merged_options(cls, params=None):
        merged = {}
        for parent in cls.__bases__:
            merged.update(parent.get_options())
        merged.update(params or {})
        return merged


class BaseExtension:
    @classmethod
    def get_options(cls):
        return {}
