#!/usr/bin/env python3
"""
    Emonoda -- The set of tools to organize and manage of your torrents
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
        name="emonoda",
        version="1.0",
        url="https://github.com/mdevaev/emonoda",
        license="GPLv3",
        author="Devaev Maxim",
        author_email="mdevaev@gmail.com",
        description="The set of tools to organize and manage of your torrents",
        platforms="any",

        packages=[
            "emlib",
            "emlib.optconf",
            "emlib.optconf.loaders",
            "emlib.apps",
            "emlib.apps.hooks",
            "emlib.plugins",
            "emlib.plugins.conveyors",
            "emlib.plugins.clients",
            "emlib.plugins.fetchers",
            "emlib.thirdparty",
        ],

        entry_points={
            "console_scripts": [
                "emdiff = emlib.apps.emdiff:main",
                "emfetch = emlib.apps.emfetch:main",
                "emfile = emlib.apps.emfile:main",
                "emload = emlib.apps.emload:main",
                "emquery = emlib.apps.emquery:main",
                "emhook-manage-trackers = emlib.apps.hooks.manage_trackers:main",
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
