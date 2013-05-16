# Copyright 2013 Databracket LLC
# See LICENSE file for details.

__author__ = "Amr Ali"
__copyright__ = "Copyright 2013 Databracket LLC"
__license__ = "GPLv3+"

"""
:module: bastio.ssh.crypto
:synopsis: A module for miscellaneous cryptographic facilities.
:author: Amr Ali <amr@databracket.com>

Configuration Store
-------------------
.. autoclass:: RSAKey
    :members:
"""

import paramiko

from bastio.mixin import public
from bastio.excepts import BastioCryptoError, reraise

@public
class RSAKey(paramiko.RSAKey):
    """A class to add a few helper functions to :class:`paramiko.RSAKey`."""

    @classmethod
    def generate(cls, size):
        """A wrapper around paramiko's RSAKey generation interface to add this
        class's methods to it.

        :param size:
            The size of the RSA key pair in bits you wish to generate.
        :type size:
            int
        :returns:
            :class:`RSAKey`
        """
        try:
            klass = paramiko.RSAKey.generate(size)
            klass.__class__ = cls
            return klass
        except Exception:
            reraise(BastioCryptoError)

    def get_private_key(self):
        """Return private key data in PEM format."""
        from StringIO import StringIO
        buf = StringIO()
        self.write_private_key(buf)
        buf.seek(0)
        return buf.read()

    def get_public_key(self):
        """Return the public key in OpenSSH authorized_keys line format."""
        return self.get_name() + ' ' + self.get_base64()

