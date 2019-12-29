#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import find_packages, setup

about = {}
with open('fabric_helpers/__about__.py') as fp:
    exec(fp.read(), about)

readme = open('README.rst').read()

setup(
    name=about['__title__'],
    version=about['__version__'],
    author=about['__author__'],
    long_description=readme,
    author_email=about['__email__'],
    description=about['__description__'],
    packages=find_packages(),
    include_package_data=True,
    license=about['__license__'],
    zip_safe=False,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
