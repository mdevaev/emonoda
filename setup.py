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
            "rtlib.optconf",
            "rtlib.optconf.loaders",
            "rtlib.apps",
            "rtlib.apps.hooks",
            "rtlib.plugins",
            "rtlib.plugins.clients",
            "rtlib.plugins.fetchers",
        ],

        entry_points={
            "console_scripts": [
                "rtdiff = rtlib.apps.rtdiff:main",
                "rtfetch = rtlib.apps.rtfetch:main",
                "rtfile = rtlib.apps.rtfile:main",
                "rthook-manage-trackers = rtlib.apps.hooks.manage_trackers:main",
            ],
        },

        install_requires=[
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
