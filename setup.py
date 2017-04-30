#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

from glob import glob
from os.path import basename
from os.path import splitext

from setuptools import find_packages
from setuptools import setup


setup(
    name="bloom_filter",
    version="1.01",
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],

    # metadata for upload to PyPI
    author="Daniel Richard Stromberg",
    author_email="strombrg@gmail.com",
    description='Pure Python Bloom Filter module',
    long_description="""
A pure python bloom filter (low storage requirement, probabilistic
set datastructure) is provided.  It is known to work on CPython 2.x,
CPython 3.x, Pypy and Jython.

Includes mmap, in-memory and disk-seek backends.

The user specifies the desired maximum number of elements and the
desired maximum false positive probability, and the module
calculates the rest.
""",
    license="MIT",
    keywords="probabilistic set datastructure",
    url='http://stromberg.dnsalias.org/~strombrg/drs-bloom-filter/',
    platforms='Cross platform',
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
    ],
)
