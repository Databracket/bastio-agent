# Copyright 2013 Databracket LLC.
# See LICENSE for details.

import os
import platform

from fabric.api import *
from bastio import __version__

def __suppress(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as ex:
        return ex

def builddeb(name="Bastio (Databracket LLC Bastio Package Signing Key)",
        email="databracket@bastio.com", dist=None):
    """Create a new debian package"""
    dist = dist if dist else platform.linux_distribution()[2]
    local('python setup.py sdist')
    __suppress(os.unlink, "debian/changelog")
    with shell_env(DEBFULLNAME=name, DEBEMAIL=email):
        local('dch --package bastio-agent --distribution {} --create -v {}'.format(
            dist, __version__))
    with settings(warn_only=True):
        local('dpkg-buildpackage -A -tc -k599FA492', capture=False)
    local('mv ../bastio-agent_{}_all.deb .'.format(__version__))
    local('mv ../bastio-agent_{}_*.changes .'.format(__version__))

def clean():
    """Clean debian package and sdist artifacts"""
    local('rm -f bastio-agent_{}_all.deb'.format(__version__))
    local('python setup.py clean')

