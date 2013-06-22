# Copyright 2013 Databracket LLC
# See LICENSE file for details.

"""
:module: bastio.test.test_ssh_api
:synopsis: Unit tests for the ssh.api module.
:author: Amr Ali <amr@databracket.com>
"""

__author__ = "Amr Ali"
__copyright__ = "Copyright 2013 Databracket LLC"
__license__ = "GPLv3+"

import os
import unittest

from bastio.ssh.api import Processor
from bastio.ssh.crypto import RSAKey
from bastio.ssh.protocol import (FeedbackMessage, AddUserMessage,
        RemoveUserMessage, UpdateUserMessage, AddKeyMessage, RemoveKeyMessage)
from bastio.concurrency import GlobalThreadPool

@unittest.skipIf(os.getuid() != 0, "this test case requires root access")
class TestProcessor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._public_key = RSAKey.generate(1024).get_public_key()
        cls._proc = Processor()

    @classmethod
    def tearDownClass(cls):
        cls._proc.stop()

    def setUp(self):
        self._add_user(FeedbackMessage.SUCCESS, sudo=False)

    def tearDown(self):
        self._remove_user(FeedbackMessage.SUCCESS)

    def test_add_remove_user(self):
        self._add_user(FeedbackMessage.INFO, sudo=False)
        self._remove_user(FeedbackMessage.SUCCESS)
        self._remove_user(FeedbackMessage.INFO)
        self._add_user(FeedbackMessage.SUCCESS, sudo=False)

    def test_add_remove_key(self):
        self._remove_user(FeedbackMessage.SUCCESS)
        self._add_key(FeedbackMessage.ERROR)
        self._add_user(FeedbackMessage.SUCCESS, sudo=False)
        self._add_key(FeedbackMessage.SUCCESS)
        self._add_key(FeedbackMessage.INFO)
        self._remove_key(FeedbackMessage.SUCCESS)
        self._remove_key(FeedbackMessage.INFO)

    def test_update_user(self):
        self._remove_user(FeedbackMessage.SUCCESS)
        self._update_user(FeedbackMessage.ERROR, sudo=False)
        self._add_user(FeedbackMessage.SUCCESS, sudo=True)
        self._update_user(FeedbackMessage.SUCCESS, sudo=True)
        self._update_user(FeedbackMessage.SUCCESS, sudo=False)
        self._update_user(FeedbackMessage.ERROR, sudo=False)

    def _add_user(self, expect_status, **kwargs):
        msg = AddUserMessage(username="test_user", **kwargs)
        self._proc_message(msg, expect_status)

    def _remove_user(self, expect_status, **kwargs):
        msg = RemoveUserMessage(username="test_user", **kwargs)
        self._proc_message(msg, expect_status)

    def _update_user(self, expect_status, **kwargs):
        msg = UpdateUserMessage(username="test_user", **kwargs)
        self._proc_message(msg, expect_status)

    def _add_key(self, expect_status, **kwargs):
        msg = AddKeyMessage(username="test_user", public_key=self._public_key,
                **kwargs)
        self._proc_message(msg, expect_status)

    def _remove_key(self, expect_status, **kwargs):
        msg = RemoveKeyMessage(username="test_user", public_key=self._public_key,
                **kwargs)
        self._proc_message(msg, expect_status)

    def _proc_message(self, msg, expect_status):
        fb = self._proc.process(msg)
        self._assert_feedback(fb, expect_status)

    def _assert_feedback(self, fb, expect_status):
        self.assertIsInstance(fb, FeedbackMessage)
        msg = "{0} != {1}: {2}".format(fb.status, expect_status, fb.feedback)
        self.assertEqual(fb.status, expect_status, msg=msg)

tests = [
        TestProcessor,
        ]

