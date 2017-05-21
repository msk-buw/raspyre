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

with open(path.join(here, 'HISTORY.rst'), encoding='utf-8') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

requirements = [
    'raspyre',
    'arrow'
]

test_requirements = [
    # TODO: put package test requirements here
    'pytest'
]

setup(
    name='raspyre-rpcserver',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    # version="0.2",
    description="RPC Server Application for the raspyre sensors framework",
    long_description=readme + '\n\n' + history,
    author="Jan Frederick Eick",
    author_email='jan-frederick.eick@uni-weimar.de',
    url='',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    entry_points={
        'console_scripts':[
            'raspyre-rpcserver=raspyre_rpcserver.RpcServer:rpc_server_main',
            ],
        },
    include_package_data=True,
    install_requires=requirements,
    license="MIT",
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements,
)
