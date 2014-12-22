import tabloid
import colorama
import pygments
import pygments.lexers
import pygments.formatters

from . import Section


# =====
def make_config_dump(config, split_by, width=None):
    table = tabloid.FormattedTable(width=width, header_background=colorama.Back.BLUE)
    table.add_column("Option", _format_option)
    table.add_column("Value", _format_value)
    table.add_column("Default", _format_default_value)
    table.add_column("Help")

    for row in _make_plain_dump(config, tuple(map(tuple, split_by))):
        if row is None:
            table.add_row((" ") * 4)
        else:
            table.add_row(row)
    return "\n".join(table.get_table())


def _format_option(name, row):
    if row[1] != row[2]:
        return "{}{}{}".format(colorama.Fore.RED, name, colorama.Style.RESET_ALL)
    return name


def _format_value(value, _):
    return pygments.highlight(
        value,
        pygments.lexers.PythonLexer(),
        pygments.formatters.TerminalFormatter(bg="dark"),
    ).replace("\n", "")


def _format_default_value(value, row):
    if row[1] != row[2]:
        return _format_value(value, None)
    else:
        return " " * len(value)


def _make_plain_dump(config, split_by=(), path=()):
    plain = []
    for (key, value) in config.items():
        if isinstance(value, Section):
            if len(plain) != 0 and path in split_by:
                plain.append(None)
            plain += _make_plain_dump(value, split_by, path + (key,))
        else:
            default = config._get_default(key)  # pylint: disable=protected-access
            plain.append((
                ".".join(path + (key,)),
                repr(value),
                repr(default),
                config._get_help(key),  # pylint: disable=protected-access
            ))
    return plain
