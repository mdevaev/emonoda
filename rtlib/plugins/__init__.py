import importlib
import functools
import os


# =====
def get_client_class(name):
    return _get_classes()["clients"][name]


def get_fetcher_class(name):
    return _get_classes()["fetchers"][name]


@functools.lru_cache()
def _get_classes():
    classes = {}
    for sub in ("clients", "fetchers"):
        classes.setdefault(sub, {})
        sub_path = os.path.join(os.path.dirname(__file__), sub)
        for file_name in os.listdir(sub_path):
            if not file_name.startswith("__") and file_name.endswith(".py"):
                module_name = file_name[:-3]
                module = importlib.import_module("rtlib.plugins.{}.{}".format(sub, module_name))
                plugin_class = getattr(module, "Plugin")
                classes[sub][plugin_class.get_name()] = plugin_class
    return classes


# =====
class BasePlugin:
    @classmethod
    def get_name(cls):
        raise NotImplementedError

    @classmethod
    def get_version(cls):
        return None

    @classmethod
    def get_options(cls):
        return {}

    @classmethod
    def get_bases(cls):
        return cls.__bases__


class BaseExtension:
    @classmethod
    def get_options(cls):
        return {}
