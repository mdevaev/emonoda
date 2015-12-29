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


# =====
def get_client_class(name):
    return _get_classes()["clients"][name]


def get_tracker_class(name):
    return _get_classes()["trackers"][name]


def get_confetti_class(name):
    return _get_classes()["confetti"][name]


@functools.lru_cache()
def _get_classes():
    classes = {}
    for sub in ("clients", "trackers", "confetti"):
        classes.setdefault(sub, {})
        sub_path = os.path.join(os.path.dirname(__file__), sub)
        for file_name in os.listdir(sub_path):
            if not file_name.startswith("__") and file_name.endswith(".py"):
                module_name = file_name[:-3]
                module = importlib.import_module("emonoda.plugins.{}.{}".format(sub, module_name))
                plugin_class = getattr(module, "Plugin")
                classes[sub][plugin_class.PLUGIN_NAME] = plugin_class
    return classes


# =====
def _get_bases(mro):
    return tuple(
        cls for cls in mro
        if set(cls.__bases__).intersection((BasePlugin, BaseExtension))
    )


class BasePlugin:
    PLUGIN_NAME = None

    @classmethod
    def get_options(cls):
        return {}

    @classmethod
    def get_bases(cls):
        return _get_bases(cls.__mro__)

    # ===

    def _init_bases(self, **kwargs):
        assert self.PLUGIN_NAME is not None
        for parent in _get_bases(self.__class__.__mro__):
            parent.__init__(self, **kwargs)

    @classmethod
    def _get_merged_options(cls, params=None):
        merged = {}
        for parent in _get_bases(cls.__mro__):
            merged.update(parent.get_options())
        merged.update(params or {})
        return merged


class BaseExtension:
    @classmethod
    def get_options(cls):
        return {}
