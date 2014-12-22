def make_config(raw, scheme, keys=()):
    if not isinstance(raw, dict):
        raise ValueError("The node '{}' must be a dictionary".format(".".join(keys) or "/"))

    config = Section()
    for (key, option) in scheme.items():
        full_key = keys + (key,)
        full_name = ".".join(full_key)

        if isinstance(option, Option):
            value = raw.get(key, option.default)
            try:
                if value is not None:
                    value = option.type(value)
            except:
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
