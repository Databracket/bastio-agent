# Copyright 2013 Databracket LLC
# See LICENSE file for details.

__author__ = "Amr Ali"
__copyright__ = "Copyright 2013 Databracket LLC"
__license__ = "GPLv3+"

"""
:module: bastio.test.test_ssh_protocol
:synopsis: Unit tests for the ssh.protocol module.
:author: Amr Ali <amr@databracket.com>
"""

import unittest
import StringIO

from bastio.ssh.protocol import Netstring

class TestNetstring(unittest.TestCase):
    def test_netstring(self):
        data = 'hello world'
        enc = Netstring.compose(data)
        res = Netstring.parse(enc)
        self.assertEqual(data, res)

        buf = StringIO.StringIO(enc)
        buf.recv = buf.read
        net = Netstring(buf)
        res = net.recv()
        self.assertEqual(data, res)

tests = [
        TestNetstring,
        ]

