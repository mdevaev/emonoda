#!/usr/bin/env python3
"""
    rtfetch -- The set of tools to organize and manage your torrents
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


import setuptools


# =====
if __name__ == "__main__":
    setuptools.setup(
        name="rtfetch",
        version="1.0",
        url="https://github.com/mdevaev/rtfetch",
        license="GPLv3",
        author="Devaev Maxim",
        author_email="mdevaev@gmail.com",
        description="The set of tools to organize and manage your torrents",
        platforms="any",

        packages=[
            "rtlib",
            "rtlib.optconf",
            "rtlib.optconf.loaders",
            "rtlib.apps",
            "rtlib.apps.hooks",
            "rtlib.plugins",
            "rtlib.plugins.conveyors",
            "rtlib.plugins.clients",
            "rtlib.plugins.fetchers",
            "rtlib.thirdparty",
        ],

        entry_points={
            "console_scripts": [
                "rtdiff = rtlib.apps.rtdiff:main",
                "rtfetch = rtlib.apps.rtfetch:main",
                "rtfile = rtlib.apps.rtfile:main",
                "rtload = rtlib.apps.rtload:main",
                "rtquery = rtlib.apps.rtquery:main",
                "rthook-manage-trackers = rtlib.apps.hooks.manage_trackers:main",
            ],
        },

        install_requires=[
            "chardet",
            "pyyaml",
            "colorama",
            "pygments",
        ],

        classifiers=[
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Development Status :: 3 - Alpha",
            "Programming Language :: Python",
            "Operating System :: OS Independent",
        ],
    )
