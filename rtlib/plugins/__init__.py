import importlib
import inspect


# =====
def get_plugin_class(sub, name):
    module = importlib.import_module("rtlib.plugins.{}.{}".format(sub, name))
    return getattr(module, "Plugin")


def get_client_class(name):
    return get_plugin_class("clients", name)


def get_fetcher_class(name):
    return get_plugin_class("fetchers", name)


def get_bases(cls):
    if not inspect.isclass(cls):
        cls = cls.__class__
    return cls.__bases__
