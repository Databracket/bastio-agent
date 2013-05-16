# Copyright 2013 Databracket LLC
# See LICENSE file for details.

__author__ = "Amr Ali"
__copyright__ = "Copyright 2013 Databracket LLC"
__license__ = "GPLv3+"

"""
:module: bastio.test.test_ssh_crypto
:synopsis: Unit tests for the ssh.crypto module.
:author: Amr Ali <amr@databracket.com>
"""

import unittest

from bastio.ssh.crypto import RSAKey
from bastio.excepts import BastioCryptoError

class TestRSAKey(unittest.TestCase):
    def test_key_generation(self):
        # Test invalid key size
        with self.assertRaises(BastioCryptoError):
            RSAKey.generate(1111)
        key = RSAKey.generate(1024)
        self.assertTrue(key.get_private_key())
        self.assertTrue(key.get_public_key())

tests = [
        TestRSAKey,
        ]

