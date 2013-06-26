#!/usr/bin/env python
# Copyright 2013 Databracket LLC
# See LICENSE file for details.

__author__ = "Amr Ali"
__copyright__ = "Copyright 2013 Databracket LLC"
__license__ = "GPLv3+"

# Make sure setuptools is installed
from distribute_setup import use_setuptools
use_setuptools()

import os
from setuptools import setup, find_packages
from bastio import __version__

def __filter_requires(filename):
    # Unnecessary packages for agent's normal operations
    unreqs = ['sphinx', 'theme', 'fabric']
    with open(filename, 'rb') as fd:
        reqs = map(lambda req: req.strip('\n'), fd.readlines())
    for unreq in unreqs:
        reqs = filter(lambda x: unreq not in x.lower(), reqs)
    return reqs

BASE_DIR = os.path.dirname(__file__)
README_PATH = os.path.join(BASE_DIR, 'README.rst')
REQS_PATH = os.path.join(BASE_DIR, 'requirements.txt')

classifiers = [
    'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Natural Language :: English',
    'Intended Audience :: Developers',
    'Intended Audience :: Information Technology',
    'Intended Audience :: System Administrators',
    'Topic :: System :: Systems Administration',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.7',
    ]

setup(
        name = 'bastio-agent',
        version = __version__,
        description = 'Bastio agent to provision system accounts and SSH access',
        long_description = file(README_PATH).read(),
        author = 'Amr Ali',
        author_email = 'amr@databracket.com',
        maintainer = 'Amr Ali',
        maintainer_email = 'amr@databracket.com',
        url = 'https://bastio.com',
        install_requires = __filter_requires(REQS_PATH),
        entry_points = {
            'console_scripts': [
                'bastio-agent = bastio.cli:bastio_main',
                ],
            },
        packages = find_packages(),
        test_suite = 'bastio.load_test_suite',
        license = 'GPLv3+',
        platforms = 'Posix',
        classifiers = classifiers,
    )

