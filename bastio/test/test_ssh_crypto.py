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

import os
import unittest

from bastio.ssh.crypto import RSAKey
from bastio.excepts import BastioCryptoError

class TestRSAKey(unittest.TestCase):
    def setUp(self):
        self._key = RSAKey.generate(1024)
        file('TEST_PRIVATE_KEY', 'wb').write(self._key.get_private_key())

    def test_key_generation(self):
        # Test invalid key size
        with self.assertRaises(BastioCryptoError):
            RSAKey.generate(1111)
        self.assertTrue(self._key.get_private_key())
        self.assertTrue(self._key.get_public_key())

    def test_key_validation(self):
        priv = self._key.get_private_key()
        self.assertTrue(RSAKey.validate_private_key(priv))
        self.assertTrue(RSAKey.validate_private_key_file('TEST_PRIVATE_KEY'))

    def tearDown(self):
        os.unlink('TEST_PRIVATE_KEY')

tests = [
        TestRSAKey,
        ]

