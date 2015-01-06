import importlib


# =====
def get_plugin_class(sub, name):
    module = importlib.import_module("rtlib.plugins.{}.{}".format(sub, name))
    return getattr(module, "Plugin")


def get_client_class(name):
    return get_plugin_class("clients", name)


def get_fetcher_class(name):
    return get_plugin_class("fetchers", name)


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
