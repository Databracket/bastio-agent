# Copyright 2013 Databracket LLC
# See LICENSE file for details.

"""
:module: bastio.log
:synopsis: Logging facilities for this project.
:author: Amr Ali <amr@databracket.com>

.. autoclass:: Logger
    :members:
"""

__author__ = "Amr Ali"
__copyright__ = "Copyright 2013 Databracket LLC"
__license__ = "GPLv3+"

import logging
import logging.handlers

from bastio.mixin import public, UniqueSingletonMeta

def _getSyslogAddress():
    import sys

    if sys.platform.startswith('linux'):
        return '/dev/log'
    elif sys.platform.startswith('darwin'):
        return '/var/run/syslog'

@public
class Logger(object):
    """A class that provides logging facilities exposed by the underlying
    Python's logging module.
    """
    __metaclass__ = UniqueSingletonMeta

    def __init__(self, prog = 'bastio-agent'):
        self._logger = logging.getLogger(prog)
        self._formatter = logging.Formatter(prog + '[%(process)d]: %(message)s')
        self._logger.addHandler(logging.NullHandler())
        self._syslog_enabled = False
        self._stream_enabled = False

    def __getattr__(self, name):
        return getattr(self._logger, name)

    def enable_syslog(self):
        """Enable Syslog logging. This method is idempotent."""
        if self._syslog_enabled:
            return
        _handler = logging.handlers.SysLogHandler(address=_getSyslogAddress(),
                facility=logging.handlers.SysLogHandler.LOG_SYSLOG)
        _handler.setFormatter(self._formatter)
        self._logger.addHandler(_handler)
        self._syslog_enabled = True

    def enable_stream(self):
        """Enable logging to STDOUT. This method is idempotent."""
        if self._stream_enabled:
            return
        _handler = logging.StreamHandler()
        _handler.setFormatter(self._formatter)
        self._logger.addHandler(_handler)
        self._stream_enabled = True

