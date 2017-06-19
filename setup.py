#!/usr/bin/env python3
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


import setuptools


# =====
if __name__ == "__main__":
    setuptools.setup(
        name="emonoda",
        version="2.0.34",
        url="https://github.com/mdevaev/emonoda",
        license="GPLv3",
        author="Devaev Maxim",
        author_email="mdevaev@gmail.com",
        description="A set of tools to organize and manage your torrents",
        platforms="any",

        packages=[
            "emonoda",
            "emonoda.web",
            "emonoda.optconf",
            "emonoda.apps",
            "emonoda.apps.hooks",
            "emonoda.apps.hooks.rtorrent",
            "emonoda.helpers",
            "emonoda.plugins",
            "emonoda.plugins.clients",
            "emonoda.plugins.trackers",
            "emonoda.plugins.confetti",
            "emonoda.thirdparty",
        ],

        package_data={
            "emonoda.plugins.confetti": ["templates/*.mako"],
        },

        entry_points={
            "console_scripts": [
                "emdiff = emonoda.apps.emdiff:main",
                "emupdate = emonoda.apps.emupdate:main",
                "emfile = emonoda.apps.emfile:main",
                "emload = emonoda.apps.emload:main",
                "emfind = emonoda.apps.emfind:main",
                "emrm = emonoda.apps.emrm:main",
                "emtest-confetti = emonoda.apps.emtest_confetti:main"
            ],
        },

        install_requires=[
            "chardet",
            "pyyaml",
            "colorama",
            "pygments",
            "pytz",
            "python-dateutil",
            "Mako",
        ],

        classifiers=[
            "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
            "Development Status :: 5 - Production/Stable",
            "Programming Language :: Python :: 3.4",
            "Programming Language :: Python :: 3.5",
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Topic :: Utilities",
            "Operating System :: OS Independent",
        ],
    )
