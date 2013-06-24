# Copyright 2013 Databracket LLC.
# See LICENSE for details.

from fabric.api import *
from bastio import __version__

def builddeb():
    """Create a new debian package"""
    local('python setup.py sdist')
    local('git log --stat > debian/changelog')
    with settings(warn_only=True):
        local('dpkg-buildpackage -A -tc', capture=False)
    local('mv ../bastio-agent_{}_all.deb .'.format(__version__))

def clean():
    """Clean debian package and sdist artifacts"""
    local('rm -f bastio-agent_{}_all.deb'.format(__version__))
    local('python setup.py clean')

