#!/usr/bin/env python
# Copyright 2013 Databracket LLC
# See LICENSE file for details.

from unittest import TextTestRunner
from distutils.core import Command, setup
from bastio.agent.test import suite as bastio_test_suite
from bastio.agent import __version__

BASE_DIR = os.path.dirname(__file__)
README = os.path.join(BASE_DIR, 'README.rst')
SCRIPT = os.path.join(BASE_DIR, 'bin', 'bastio-agent')

class TestCommand(Command):
    user_options = []
    description = "Run all unit tests"

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        t = TextTestRunner(verbosity = 2)
        t.run(bastio_test_suite)

packages = [
    'bastio',
    'bastio.agent',
    'bastio.agent.test',
    ]

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
        long_description = file(README).read(),
        author = 'Amr Ali',
        author_email = 'amr@databracket.com',
        maintainer = 'Amr Ali',
        maintainer_email = 'amr@databracket.com',
        url = 'https://bastio.com',
        scripts = [SCRIPT],
        packages = packages,
        license = 'GPLv3+',
        platforms = 'Posix',
        classifiers = classifiers,
        cmdclass = {'test', TestCommand},
    )
