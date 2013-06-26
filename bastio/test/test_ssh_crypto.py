# Copyright 2013 Databracket LLC
# See LICENSE file for details.

"""
:module: bastio.test.test_ssh_crypto
:synopsis: Unit tests for the ssh.crypto module.
:author: Amr Ali <amr@databracket.com>
"""

__author__ = "Amr Ali"
__copyright__ = "Copyright 2013 Databracket LLC"
__license__ = "GPLv3+"

import os
import unittest

from bastio.ssh.crypto import RSAKey
from bastio.excepts import BastioCryptoError

class TestRSAKey(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = RSAKey.generate(1024)
        cls.key_file = 'TEST_PRIVATE_KEY'
        file(cls.key_file, 'wb').write(cls.key.get_private_key())

    @classmethod
    def tearDownClass(cls):
        os.unlink(cls.key_file)

    def test_key_generation(self):
        # Test invalid key size
        with self.assertRaises(BastioCryptoError):
            RSAKey.generate(1111)
        self.assertTrue(self.key.get_private_key())
        self.assertTrue(self.key.get_public_key())

    def test_key_validation(self):
        priv = self.key.get_private_key()
        self.assertTrue(RSAKey.validate_private_key(priv))
        self.assertTrue(RSAKey.validate_private_key_file('TEST_PRIVATE_KEY'))
        self.assertTrue(RSAKey.validate_public_key(self.key.get_public_key()))

    def test_key_loading(self):
        pubkey = self.key.get_public_key()
        self.assertIsInstance(RSAKey.from_public_key(pubkey), RSAKey)

tests = [
        TestRSAKey,
        ]

