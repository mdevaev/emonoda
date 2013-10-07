#!/usr/bin/env python2
# -*- coding: utf-8 -*-


from setuptools import setup


setup(
	name="rtfetch",
	version="0.1",
	url="https://github.com/mdevaev/rtfetch",
	license="GPLv3",
	author="Devaev Maxim",
	author_email="mdevaev@gmail.com",
	description="rtfetch -- The set of tools to organize and managament of your torrents",
	platforms="any",
	packages=[
		"rtlib",
		"rtlib/fetchers",
		"rtlib/clients",
	],
	scripts=[
		"rtfetch.py",
		"rtquery.py",
		"rtload.py",
		"rtfile.py",
		"rtdiff.py",
		"rthook-manage-trackers.py",
	],
	classifiers=[
		"Topic :: Software Development :: Libraries :: Python Modules",
		"Development Status :: 3 - Alpha",
		"Programming Language :: Python",
		"Operating System :: OS Independent",
	],
)

