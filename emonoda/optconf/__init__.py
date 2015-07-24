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


import json


# =====
def build_raw_from_options(options):
    raw = {}
    for option in options:
        (key, value) = (option.split("=", 1) + [None])[:2]
        if len(key.strip()) == 0:
            raise ValueError("Empty option key (required 'key=value' instead of '{}')".format(option))
        if value is None:
            raise ValueError("No value for key '{}'".format(key))

        section = raw
        subs = list(map(str.strip, key.split("/")))
        for sub in subs[:-1]:
            section.setdefault(sub, {})
            section = section[sub]
        section[subs[-1]] = _parse_value(value)
    return raw


def _parse_value(value):
    value = value.strip()
    if (
        not value.isdigit()
        and value not in ("true", "false", "null")
        and not value.startswith("{")
        and not value.startswith("[")
        and not value.startswith("\"")
    ):
        value = "\"{}\"".format(value)
    return json.loads(value)


# =====
def make_config(raw, scheme, keys=()):
    if not isinstance(raw, dict):
        raise ValueError("The node '{}' must be a dictionary".format("/".join(keys) or "/"))

    config = Section()
    for (key, option) in scheme.items():
        full_key = keys + (key,)
        full_name = "/".join(full_key)

        if isinstance(option, Option):
            value = raw.get(key, option.default)
            try:
                value = option.type(value)
            except Exception:
                raise ValueError("Invalid value '{value}' for key '{key}'".format(key=full_name, value=value))
            config[key] = value
            config._set_meta(  # pylint: disable=protected-access
                name=key,
                secret=isinstance(option, SecretOption),
                default=option.default,
                help=option.help,
            )
        elif isinstance(option, dict):
            config[key] = make_config(raw.get(key, {}), option, full_key)
        else:
            raise RuntimeError("Incorrect scheme definition for key '{}':"
                               " the value is {}, not dict or [Secret]Option()".format(full_name, type(option)))
    return config


class Section(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self._meta = {}

    def _set_meta(self, name, secret, default, help):  # pylint: disable=redefined-builtin
        self._meta[name] = {
            "secret":  secret,
            "default": default,
            "help":    help,
        }

    def _is_secret(self, name):
        return self._meta[name]["secret"]

    def _get_default(self, name):
        return self._meta[name]["default"]

    def _get_help(self, name):
        return self._meta[name]["help"]

    def __getattribute__(self, name):
        if name in self:
            return self[name]
        else:  # For pickling
            return dict.__getattribute__(self, name)


_type = type


class Option:
    def __init__(self, default, help, type=None):  # pylint: disable=redefined-builtin
        self.default = default
        self.help = help
        self.type = type or (_type(default) if default is not None else str)

    def __repr__(self):
        return "<Option(default={self.default}, type={self.type}, help={self.help})>".format(self=self)


class SecretOption(Option):
    pass
