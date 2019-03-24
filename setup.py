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


from setuptools import setup
from setuptools.extension import Extension

from Cython.Build import cythonize


# =====
def main() -> None:
    with open("requirements.txt") as requirements_file:
        install_requires = list(filter(None, requirements_file.read().splitlines()))

    setup(
        name="emonoda",
        version="2.1.26",
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
            "emonoda.apps.hooks.transmission",
            "emonoda.helpers",
            "emonoda.plugins",
            "emonoda.plugins.clients",
            "emonoda.plugins.trackers",
            "emonoda.plugins.confetti",
            "emonoda.thirdparty",
        ],

        package_data={
            "emonoda.plugins.confetti": ["templates/*.mako"],
            "emonoda.thirdparty": ["bencoder.pyx"],
        },

        entry_points={
            "console_scripts": [
                "emdiff = emonoda.apps.emdiff:main",
                "emupdate = emonoda.apps.emupdate:main",
                "emfile = emonoda.apps.emfile:main",
                "emload = emonoda.apps.emload:main",
                "emfind = emonoda.apps.emfind:main",
                "emrm = emonoda.apps.emrm:main",
                "emconfetti-demo = emonoda.apps.emconfetti_demo:main",
                "emconfetti-tghi = emonoda.apps.emconfetti_tghi:main",
                "emhook-rtorrent-collectd-stat = emonoda.apps.hooks.rtorrent.collectd_stat:main",
                "emhook-rtorrent-manage-trackers = emonoda.apps.hooks.rtorrent.manage_trackers:main",
                "emhook-transmission-redownload = emonoda.apps.hooks.transmission.redownload:main",
            ],
        },

        ext_modules=cythonize(Extension(
            "emonoda.thirdparty.bencoder",
            ["emonoda/thirdparty/bencoder.pyx"],
            extra_compile_args=["-O3"],
        )),

        install_requires=install_requires,

        classifiers=[
            "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
            "Development Status :: 5 - Production/Stable",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Cython",
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Topic :: Communications :: File Sharing",
            "Topic :: Internet :: WWW/HTTP",
            "Topic :: Utilities",
            "Operating System :: OS Independent",
            "Intended Audience :: System Administrators",
            "Intended Audience :: End Users/Desktop",
        ],
    )


if __name__ == "__main__":
    main()
