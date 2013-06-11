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
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.7',
    ]

setup(
        name = 'Bastio-Agent',
        version = __version__,
        description = 'Bastio agent to provision system accounts and SSH access',
        long_description = file(README_PATH).read(),
        author = 'Amr Ali',
        author_email = 'amr@databracket.com',
        maintainer = 'Amr Ali',
        maintainer_email = 'amr@databracket.com',
        url = 'https://bastio.com',
        install_requires = map(lambda req: req.strip('\n'), file(REQS_PATH).readlines()),
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

