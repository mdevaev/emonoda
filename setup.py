#!/usr/bin/env python2
# -*- coding: utf-8 -*-


from rtlib import const

import setuptools


##### Main #####
if __name__ == "__main__" :
	setuptools.setup(
		name="rtfetch",
		version=const.VERSION,
		url=const.UPSTREAM_URL,
		license="GPLv3",
		author="Devaev Maxim",
		author_email="mdevaev@gmail.com",
		description="The set of tools to organize and managament of your torrents",
		platforms="any",

		packages=(
			"rtlib",
			"rtlib/fetchers",
			"rtlib/clients",
		),

		scripts=(
			"rtfetch.py",
			"rtquery.py",
			"rtload.py",
			"rtfile.py",
			"rtdiff.py",
			"rthook-manage-trackers.py",
		),

		classifiers=(
			"Topic :: Software Development :: Libraries :: Python Modules",
			"Development Status :: 3 - Alpha",
			"Programming Language :: Python",
			"Operating System :: OS Independent",
		),
	)

