# Copyright 2013 Databracket LLC.
# See LICENSE file for details.

"""
:module: bastio
:synopsis: Bastio's agent package.
:author: Amr Ali <amr@databracket.com>

CLI Management
--------------
.. automodule:: bastio.cli

SSH And Communication Management
--------------------------------
.. automodule:: bastio.ssh

Account Operations
------------------
.. automodule:: bastio.account

Configuration Utilities
-----------------------
.. automodule:: bastio.configs

Concurrency Utilities
---------------------
.. automodule:: bastio.concurrency

Logging Facility
----------------
.. automodule:: bastio.log

Mixins And Language Helpers
---------------------------
.. automodule:: bastio.mixin

Version Information
-------------------
.. automodule:: bastio.version

Exceptions
----------
.. automodule:: bastio.excepts
"""

__author__ = "Amr Ali"
__copyright__ = "Copyright 2013 Databracket LLC"
__license__ = "GPLv3+"

from .version import __version__

def load_test_suite():
    from bastio.test import suite
    return suite

