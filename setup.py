#!/usr/bin/env python3


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
        description="The set of tools to organize and managament for your torrents",
        platforms="any",

        namespace_packages=[
            "rtlib",
            "rtlib.clients",
        ],

        packages=[
            "rtlib.core",
            "rtlib.clients.rtorrent",
            "rtlib.optconf",
            "rtlib.optconf.loaders",
        ],

        install_requires=[
            "ulib",
            "bcoding",
            "colorama",

            "tabloid",
            "pygments",
            "pyyaml",
            "contextlog",
        ],

        classifiers=[
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Development Status :: 3 - Alpha",
            "Programming Language :: Python",
            "Operating System :: OS Independent",
        ],
    )
