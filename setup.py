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
	description="rtfetch -- Update rtorrent files from popular trackers",
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
		"rthook-manage-trackers.py",
	],
	classifiers=[
		"Topic :: Software Development :: Libraries :: Python Modules",
		"Development Status :: 3 - Alpha",
		"Programming Language :: Python",
		"Operating System :: OS Independent",
	],
)

