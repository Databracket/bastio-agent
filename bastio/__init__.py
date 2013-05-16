# Copyright 2013 Databracket LLC.
# See LICENSE file for details.

__author__ = "Amr Ali"
__copyright__ = "Copyright 2013 Databracket LLC"
__license__ = "GPLv3+"

"""
:module: bastio
:synopsis: Bastio's agent package.
:author: Amr Ali <amr@databracket.com>
"""

from .version import __version__

def load_test_suite():
    from bastio.test import suite
    return suite
