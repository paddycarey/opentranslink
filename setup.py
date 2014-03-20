#!/usr/bin/env python
# -*- coding: utf-8 -*-
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


setup(
    name='opentranslink',
    version='0.0.1',
    description='The OpenTranslink project aims to provide a simple pythonic interface to public data on translink.co.uk e.g. timetables',
    long_description=open('README.rst').read(),
    author='Patrick Carey',
    author_email='paddy@wackwack.co.uk',
    url='https://github.com/paddycarey/opentranslink',
    packages=[
        'opentranslink',
    ],
    package_dir={'opentranslink': 'opentranslink'},
    include_package_data=True,
    install_requires=[
        'beautifulsoup4>=4',
        'requests>=2',
        'tablib',
    ],
    license="MIT",
    zip_safe=False,
    keywords='opentranslink',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
    test_suite='tests',
)
