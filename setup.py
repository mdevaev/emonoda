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
        description="The set of tools to organize and manage your torrents",
        platforms="any",

        packages=[
            "rtlib",
            "rtlib.core",
            "rtlib.optconf",
            "rtlib.optconf.loaders",
            "rtlib.apps",
            "rtlib.apps.hooks",
            "rtlib.plugins",
            "rtlib.plugins.clients",
            "rtlib.plugins.fetchers",
        ],

        install_requires=[
            "bcoding",
            "colorama",

            "tabloid",
            "pygments",
            "pyyaml",
        ],

        classifiers=[
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Development Status :: 3 - Alpha",
            "Programming Language :: Python",
            "Operating System :: OS Independent",
        ],
    )
