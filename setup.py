#!/usr/bin/env python3
"""
    Emonoda -- The set of tools to organize and manage your torrents
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
        version="1.7.0",
        url="https://github.com/mdevaev/emonoda",
        license="GPLv3",
        author="Devaev Maxim",
        author_email="mdevaev@gmail.com",
        description="The set of tools to organize and manage your torrents",
        platforms="any",

        packages=[
            "emonoda",
            "emonoda.optconf",
            "emonoda.optconf.loaders",
            "emonoda.apps",
            "emonoda.apps.hooks",
            "emonoda.plugins",
            "emonoda.plugins.conveyors",
            "emonoda.plugins.clients",
            "emonoda.plugins.fetchers",
            "emonoda.thirdparty",
        ],

        entry_points={
            "console_scripts": [
                "emdiff = emonoda.apps.emdiff:main",
                "emfetch = emonoda.apps.emfetch:main",
                "emfile = emonoda.apps.emfile:main",
                "emload = emonoda.apps.emload:main",
                "emfind = emonoda.apps.emfind:main",
                "emhook-manage-trackers = emonoda.apps.hooks.manage_trackers:main",
            ],
        },

        install_requires=[
            "chardet",
            "pyyaml",
            "colorama",
            "pygments",
        ],

        classifiers=[
            "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
            "Development Status :: 5 - Production/Stable",
            "Programming Language :: Python :: 3.4",
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Topic :: Utilities",
            "Operating System :: OS Independent",
        ],
    )
