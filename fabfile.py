# Copyright 2013 Databracket LLC.
# See LICENSE for details.

import os
import tempfile
import platform
import shutil
from fabric.api import *

from bastio import __version__

ROOT_DIR = os.path.dirname(__file__)
DIST_DIR = os.path.join(ROOT_DIR, 'dist')
DEBIAN_DIR = os.path.join(ROOT_DIR, 'debian')
DATA_DIR = os.path.join(ROOT_DIR, 'data')

def __suppress(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as ex:
        return ex

def builddeb(name, email, dist=None, pkg_version='1', keyid='599FA492'):
    """Create a new debian package"""
    dist = dist if dist else platform.linux_distribution()[2]
    version = "{}-{}".format(__version__, pkg_version)
    dch_args = ['dch']
    if os.path.exists(os.path.join(DEBIAN_DIR, 'changelog')):
        dch_args.append('-i')
    else:
        dch_args.append('--create')
        dch_args.append('--package bastio-agent')
        dch_args.append('--distribution {}'.format(dist))
        dch_args.append('-v {}'.format(version))

    # Add an entry to the changelog and prepare the distribution tar-ball
    with lcd(ROOT_DIR):
        local('python setup.py sdist')
        with shell_env(DEBFULLNAME=name, DEBEMAIL=email):
            local(' '.join(dch_args))

    # Prepare the source package environment
    tempdir = tempfile.mkdtemp()
    environdir = os.path.join(tempdir, 'environ')
    os.mkdir(environdir)
    shutil.copytree(DEBIAN_DIR, os.path.join(environdir, 'debian'))
    shutil.copytree(DATA_DIR, os.path.join(environdir, 'data'))
    shutil.copytree(DIST_DIR, os.path.join(environdir, 'dist'))

    # Build a source package
    with lcd(environdir):
        local('dpkg-buildpackage -S -tc -k{}'.format(keyid), capture=False)

    # Move result to the root directory of the repository
    with lcd(tempdir):
        local('mv bastio-agent_{}* {}'.format(__version__, ROOT_DIR))

    # Clean up the temporary environment
    __suppress(shutil.rmtree, tempdir)

def uploaddeb(ppa="ppa:databracket/bastio-agent"):
    """Upload the latest source package to Launchpad"""
    with lcd(ROOT_DIR):
        #local("dput {} bastio-agent_{}*_source.changes".format(ppa, __version__))
        local ("dupload -c  --to bastio bastio-agent_{}*_source.changes".format(__version__))

def clean():
    """Clean debian package and sdist artifacts"""
    with lcd(ROOT_DIR):
        local('rm -f bastio-agent_{}*'.format(__version__))
        local('python setup.py clean')

