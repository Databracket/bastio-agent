# Copyright 2013 Databracket LLC
# See LICENSE file for details.

__author__ = "Amr Ali"
__copyright__ = "Copyright 2013 Databracket LLC"
__license__ = "GPLv3+"

"""
:module: bastio.excepts
:synopsis: Exception classes used by this project.
:author: Amr Ali <amr@databracket.com>

Exceptions
----------
.. automethod:: reraise

.. autoclass:: BastioException

.. autoclass:: BastioConfigError

.. autoclass:: BastioUnimplementedError
"""

import sys

from bastio.mixin import public

@public
def reraise(ex, message=None):
    """Reraise the exception last happened with the original traceback.

    :param ex:
        The exception to be raised instead of the original one.
    :type ex:
        A subclass of Exception.
    :param message:
        An optional message to replace the old exception's message.
    :type message:
        str
    :raises:
        ``ex``
    """
    (_, msg, tb) = sys.exc_info()
    msg = message if message else msg
    raise ex, msg, tb

@public
class BastioException(Exception):
    """A Bastio general exception"""
    pass

@public
class BastioConfigError(BastioException):
    """A configuration operation error"""
    pass

@public
class BastioUnimplementedError(BastioException):
    """An unimplemented operation error"""
    pass

