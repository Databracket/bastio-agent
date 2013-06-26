# Copyright 2013 Databracket LLC
# See LICENSE file for details.

"""
:module: bastio.ssh.crypto
:synopsis: A module for miscellaneous cryptographic facilities.
:author: Amr Ali <amr@databracket.com>

.. autoclass:: RSAKey
    :members:
"""

__author__ = "Amr Ali"
__copyright__ = "Copyright 2013 Databracket LLC"
__license__ = "GPLv3+"

import base64
import StringIO
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

    @classmethod
    def from_public_key(cls, public_key):
        """Load an instance of this class with ``public_key``.

        :param public_key:
            An OpenSSH formatted public key.
        :type public_key:
            str
        :returns:
            :class:`RSAKey`
        """
        if not cls.validate_public_key(public_key):
            raise BastioCryptoError("invalid public key")
        vals = public_key.split(' ')
        return cls(data=base64.decodestring(vals[1]))

    @classmethod
    def validate_public_key(cls, data):
        """Validate public key data.

        :param data:
            An OpenSSH formatted public key.
            [ssh-][ALGO][ ][BASE64][ ][COMMENT]
        :type data:
            str
        :returns:
            Whether the key data is valid.
        """
        try:
            if not data.startswith('ssh-'):
                return False
            vals = data.split(' ')
            if len(vals) < 2: # There must be at least 'ssh-algo' and 'base64'
                return False
            cls(data=base64.decodestring(vals[1]))
            return True
        except Exception:
            return False

    @classmethod
    def validate_private_key(cls, data):
        """Validate private key data.

        :param data:
            A PEM formatted private key content.
        :type data:
            str
        :returns:
            Whether the key data is valid.
        """
        try:
            buf = StringIO.StringIO(data)
            cls.from_private_key(buf)
            return True
        except Exception:
            return False

    @classmethod
    def validate_private_key_file(cls, filename):
        """Validate private key file.

        :param filename:
            A filename that contains PEM formatted private key data.
        :type filename:
            str
        :returns:
            Whether the key file is valid.
        """
        try:
            cls.from_private_key_file(filename)
            return True
        except Exception:
            return False

    def get_private_key(self):
        """Return private key data in PEM format."""
        buf = StringIO.StringIO()
        self.write_private_key(buf)
        buf.seek(0)
        return buf.read()

    def get_public_key(self):
        """Return the public key in OpenSSH authorized_keys line format."""
        return self.get_name() + ' ' + self.get_base64()

