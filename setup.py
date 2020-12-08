#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os
import json
import imp

from setuptools import setup, find_packages

PROJ_NAME = 'aio_downloader'
PACKAGE_NAME = 'aio_downloader'
PROJ_METADATA = '%s.json' % PROJ_NAME

here = os.path.abspath(os.path.dirname(__file__))
proj_info = json.loads(open(os.path.join(here, PROJ_METADATA), encoding='utf-8').read())
try:
    README = open(os.path.join(here, 'README.md'), encoding='utf-8').read()
except:
    README = ""
VERSION = imp.load_source('version', os.path.join(here, '%s/__init__.py' % PACKAGE_NAME)).__version__

setup(
    name=proj_info.get('name'),
    version=VERSION,
    description=proj_info.get('description'),
    long_description=README,
    classifiers=proj_info.get('classifiers'),
    entry_points={
        'console_scripts': proj_info.get('console_scripts')
    },
    keywords=proj_info.get('keywords'),
    author=proj_info.get('author'),
    author_email=proj_info.get('author_email'),
    url=proj_info.get('url'),
    license=proj_info.get('license'),
    packages=find_packages(),
    install_requires=proj_info.get('install_requires'),
    include_package_data=True,
    zip_safe=True,
)