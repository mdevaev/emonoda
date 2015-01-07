"""
    Description: makes pretty table in console
    Upstream: https://github.com/shoonoise/Tabloid
    License: GPL (?)

    Copyright (c) 2014 Alexander Kushnarev
"""

# flake8: noqa


import shutil
import sys
from itertools import zip_longest
from colorama import Style, Back


class FormattedTable:
    def __init__(self, width=None, padding=1, fill_symbol=' ', header_background=Back.GREEN):
        self._terminal_width = width or self._get_terminal_size()
        self._header_background = header_background
        self._padding = padding
        self._fill_symbol = fill_symbol
        self._table = []

    @staticmethod
    def _get_terminal_size():
        try:
            return shutil.get_terminal_size()[0]
        except AttributeError:
            import fcntl
            import termios
            import struct

            gwinsz = struct.pack("HHHH", 0, 0, 0, 0)

            try:
                gwinsz = fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, gwinsz)
            except Exception:
                pass
            _, columns = struct.unpack("HHHH", gwinsz)[:2]
            return columns

    def _get_header_width(self):
        """
        Calculate total header width:
        (sum of width of each (column + padding)) + header padding
        """
        return sum(map(lambda x: self._padding + x,
                       (column['max_width'] if column['max_width'] else column['width']
                        for column in self._table))) + self._padding

    def _fill_up_string(self, string, width):
        indent = self._fill_symbol * self._padding
        fill = self._fill_symbol * (width - (len(string) + self._padding))
        return '{}{}{}'.format(indent, string, fill)

    def _align_head(self):
        header = ''
        tile = self._terminal_width
        for column in self._table:
            width = column['width'] + self._padding
            title = column['title']
            if width < tile:
                tile -= width
            else:
                width = tile - self._padding * len(self._table)
                column['width'] = width
            header += self._fill_up_string(title, width)
        return header + self._fill_symbol * self._padding

    def _get_sliced_elements(self, elem, column_number):
        """
        Slice string longer than column's width to n lines with width equals to column's width
        """
        column_width = self._table[column_number]['width']
        if len(elem) < column_width + self._padding:
            return [elem]
        return [elem[x:x+column_width] for x in range(0, len(elem), column_width)]

    def _format_row(self, row):
        """
        Align, slice and format row
        """
        for multiline_cells in zip_longest(*[self._get_sliced_elements(elem, column_number)
                                             for column_number, elem in enumerate(row)], fillvalue=self._fill_symbol):
            formatted_row = ''
            for column_number, line in enumerate(multiline_cells):
                format_function = self._table[column_number]['formatter']
                needed_with = self._table[column_number]['width'] + self._padding
                if format_function is None:
                    format_function = lambda x, _: x
                formatted_row += format_function(self._fill_up_string(line, needed_with), row)
            yield formatted_row

    def _get_rows(self):
        for row in zip(*[column['lines'] for column in self._table]):
            # Python < 3.3 can't into `yeild from`
            for _ in self._format_row(row):
                yield _

    def add_column(self, name, formatter=None, max_width=None):
        """
        Add column to the table (table's header)
        """
        self._table.append({'title': name,
                            'width': len(name),
                            'max_width': max_width,
                            'formatter': formatter,
                            'lines': []})
        assert self._terminal_width >= self._get_header_width(), "Header's width can't be over than terminal's size."

    def add_row(self, row):
        """
        Add row in the table
        """
        for column_number, line in enumerate(row):
            line = str(line)
            max_width = self._table[column_number]['max_width']
            column_width = self._table[column_number]['width']
            self._table[column_number]['lines'].append(line)
            if column_width < len(line):
                if max_width is None:
                    self._table[column_number]['width'] = len(line)
                else:
                    if max_width < column_width:
                        raise RuntimeError("Max width can't be less than column name + padding: {}.".format(
                            self._padding + column_width))
                    self._table[column_number]['width'] = max_width

    def get_table(self):
        header = '{}{}{}'.format(self._header_background,
                                 self._align_head(),
                                 Style.RESET_ALL)
        body = '\n'.join(self._get_rows())
        return header, body
