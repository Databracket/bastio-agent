# Copyright 2013 Databracket LLC.
# See LICENSE file for details.

"""
.. rst-class:: html-toggle

CLI Management
--------------
.. automodule:: bastio.cli

.. rst-class:: html-toggle

SSH And Communication Management
--------------------------------
.. automodule:: bastio.ssh

.. rst-class:: html-toggle

Account Operations
------------------
.. automodule:: bastio.account

.. rst-class:: html-toggle

Configuration Utilities
-----------------------
.. automodule:: bastio.configs

.. rst-class:: html-toggle

Concurrency Utilities
---------------------
.. automodule:: bastio.concurrency

.. rst-class:: html-toggle

Logging Facility
----------------
.. automodule:: bastio.log

.. rst-class:: html-toggle

Mixins And Language Helpers
---------------------------
.. automodule:: bastio.mixin

.. rst-class:: html-toggle

Version Information
-------------------
.. automodule:: bastio.version

.. rst-class:: html-toggle

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

