#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This code is distributed under the two-clause BSD license.
# Copyright (c) 2012 Raphaël Barrois

from setuptools import setup
import os
import re

root_dir = os.path.abspath(os.path.dirname(__file__))


def get_version(package_name):
    version_re = re.compile(r"^__version__ = [\"']([\w_.-]+)[\"']$")
    package_components = package_name.split('.')
    path_components = package_components + ['__init__.py']
    with open(os.path.join(root_dir, *path_components)) as f:
        for line in f:
            match = version_re.match(line[:-1])
            if match:
                return match.groups()[0]
    return '0.1.0'


PACKAGE = 'confutils'


setup(
    name="confutils",
    version=get_version(PACKAGE),
    author="Raphaël Barrois",
    author_email="raphael.barrois+confutils@polytechnique.org",
    description="Advanced configuration file utilities.",
    license="BSD",
    keywords=['project', 'library', 'template'],
    url="http://github.com/rbarrois/confutils",
    download_url="http://pypi.python.org/pypi/confutils/",
    packages=['confutils'],
    setup_requires=[
        'distribute',
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    test_suite='tests',
)

