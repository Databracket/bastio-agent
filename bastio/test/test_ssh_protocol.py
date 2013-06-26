# Copyright 2013 Databracket LLC
# See LICENSE file for details.

"""
:module: bastio.test.test_ssh_protocol
:synopsis: Unit tests for the ssh.protocol module.
:author: Amr Ali <amr@databracket.com>
"""

__author__ = "Amr Ali"
__copyright__ = "Copyright 2013 Databracket LLC"
__license__ = "GPLv3+"

import unittest
import StringIO

from bastio.mixin import Json
from bastio.excepts import BastioMessageError
from bastio.ssh.crypto import RSAKey
from bastio.ssh.protocol import (Netstring, MessageParser, ProtocolMessage,
        FeedbackMessage, ActionMessage, AddUserMessage, RemoveUserMessage,
        UpdateUserMessage, AddKeyMessage, RemoveKeyMessage, ActionParser)

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

class TestProtocolMessages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pubkey = RSAKey.generate(1024).get_public_key()

    def test_message_add_user(self):
        obj = self._construct_action_msg(AddUserMessage)
        self._msg_parser_raises(obj)
        obj.sudo = False
        msg = MessageParser.parse(obj.to_json())
        self.assertIsInstance(msg, AddUserMessage)

    def test_message_remove_user(self):
        obj = self._construct_action_msg(RemoveUserMessage)
        msg = MessageParser.parse(obj.to_json())
        self.assertIsInstance(msg, RemoveUserMessage)

    def test_message_update_user(self):
        obj = self._construct_action_msg(UpdateUserMessage)
        self._msg_parser_raises(obj)
        obj.sudo = False
        msg = MessageParser.parse(obj.to_json())
        self.assertIsInstance(msg, UpdateUserMessage)

    def test_message_add_key(self):
        obj = self._construct_action_msg(AddKeyMessage)
        self._msg_parser_raises(obj)
        obj.public_key = self.pubkey
        msg = MessageParser.parse(obj.to_json())
        self.assertIsInstance(msg, AddKeyMessage)

    def test_message_remove_key(self):
        obj = self._construct_action_msg(RemoveKeyMessage)
        self._msg_parser_raises(obj)
        obj.public_key = self.pubkey
        msg = MessageParser.parse(obj.to_json())
        self.assertIsInstance(msg, RemoveKeyMessage)

    def test_message_feedback(self):
        obj = self._construct_protocol_msg()
        obj.type = FeedbackMessage.MessageType
        self._msg_parser_raises(obj)
        obj.feedback = "test"
        self._msg_parser_raises(obj)
        obj.status = 31337 # invalid status
        self._msg_parser_raises(obj)
        obj.status = FeedbackMessage.INFO
        msg = MessageParser.parse(obj.to_json())
        self.assertIsInstance(msg, FeedbackMessage)

    def test_message_reply(self):
        obj = self._construct_action_msg(RemoveUserMessage)
        msg = MessageParser.parse(obj.to_json())
        fb = msg.reply("test success", FeedbackMessage.SUCCESS)
        self.assertIsInstance(fb, FeedbackMessage)
        self.assertEqual(fb.feedback, "test success")
        self.assertEqual(fb.status, FeedbackMessage.SUCCESS)
        fb = msg.reply("test warning", FeedbackMessage.WARNING)
        self.assertIsInstance(fb, FeedbackMessage)
        self.assertEqual(fb.feedback, "test warning")
        self.assertEqual(fb.status, FeedbackMessage.WARNING)
        self.assertEqual(fb.mid, msg.mid)
        fb.to_json()

    def test_message_username(self):
        obj = self._construct_action_msg(AddUserMessage, username='@@@@23#$@FE__')
        self._msg_parser_raises(obj)
        obj.sudo = False
        self._msg_parser_raises(obj)

    def _msg_parser_raises(self, obj):
        with self.assertRaises(BastioMessageError):
            MessageParser.parse(obj.to_json())

    def _construct_protocol_msg(self):
        obj = Json()
        obj.mid = "234293472786"
        self._msg_parser_raises(obj)
        return obj

    def _construct_action_msg(self, action, username='d4de'):
        obj = self._construct_protocol_msg()
        obj.type = ActionMessage.MessageType
        self._msg_parser_raises(obj)
        obj.action = action.ActionType
        self._msg_parser_raises(obj)
        obj.username = username
        return obj

tests = [
        TestNetstring,
        TestProtocolMessages,
        ]

