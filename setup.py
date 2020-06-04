#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A setuptools based setup module for Raspyre"""

from codecs import open
from os import path
from setuptools import setup, find_packages

import versioneer

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as readme_file:
    readme = readme_file.read()

requirements = [
]

test_requirements = [
    'pytest'
]

setup(
    name='raspyre',
    cmdclass=versioneer.get_cmdclass(),
    version="2.1",
    description="Raspyre Software Framework for SHM applications",
    long_description=readme,
    author="Jan Frederick Eick",
    author_email='jan-frederick.eick@uni-weimar.de',
    url='',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    entry_points={
        'console_scripts':[
            'raspyre-rpcserver=raspyre.rpc.server:main',
            'raspyre-converter=raspyre.converter:main',
            ],
        },
    include_package_data=True,
    install_requires=requirements,
    license="GPLv3",
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    test_suite='tests',
    tests_require=test_requirements,
)
