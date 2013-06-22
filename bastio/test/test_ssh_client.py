# Copyright 2013 Databracket LLC
# See LICENSE file for details.

"""
:module: bastio.test.test_ssh_client
:synopsis: Unit tests for the ssh.client module.
:author: Amr Ali <amr@databracket.com>
"""

__author__ = "Amr Ali"
__copyright__ = "Copyright 2013 Databracket LLC"
__license__ = "GPLv3+"

import unittest
import threading
import paramiko
import socket
import logging
import Queue as queue

from bastio.configs import GlobalConfigStore
from bastio.ssh.client import BackendConnector
from bastio.ssh.crypto import RSAKey
from bastio.ssh.protocol import (Netstring, MessageParser, AddUserMessage,
        FeedbackMessage)
from bastio.excepts import (BastioNetstringError, BastioMessageError,
        BastioEOFError)

# Disable paramiko logging
__plog = logging.getLogger('paramiko')
__plog.addHandler(logging.NullHandler())

class SSHSubsystem(paramiko.SubsystemHandler):
    def start_subsystem(self, name, transport, chan):
        while True:
            try:
                json_string = self._read_message(chan)
                msg = MessageParser.parse(json_string)
                reply = msg.reply("message received successfully",
                        FeedbackMessage.SUCCESS)
                self._write_message(chan, reply.to_json())
                return
            except BastioNetstringError as ex:
                msg = FeedbackMessage(ex.message, FeedbackMessage.ERROR)
                self._write_message(chan, msg.to_json())
                return
            except BastioMessageError as ex:
                msg = FeedbackMessage(ex.message, FeedbackMessage.ERROR)
                self._write_message(chan, msg.to_json())
                return
            except BastioEOFError:
                return

    @staticmethod
    def _read_message(chan):
        nets = Netstring(chan)
        return nets.recv()

    @staticmethod
    def _write_message(chan, data):
        nets = Netstring.compose(data)
        remaining = len(nets)
        while remaining > 0:
            n = chan.send(nets)
            if n <= 0:
                raise BastioEOFError("channel closed")
            remaining -= n

class SSHServer(paramiko.ServerInterface):
    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_publickey(self, username, key):
        cfg = GlobalConfigStore()
        if (username == cfg.agent_username) and (key == cfg.agentkey):
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return 'publickey'

class TestBackendConnector(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Prepare server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('127.0.0.1', 12345))
        sock.listen(10)
        cls.server_sock = sock
        th = threading.Thread(target=cls.__server)
        th.setDaemon(True)
        th.start()
        cls.server_thread = th
        cls.server_ready = threading.Event()
        cls.server_end = threading.Event()

        # Prepare BackendConnector
        cfg = GlobalConfigStore()
        cfg.agent_username = "test_agent"
        cfg.agentkey = RSAKey.generate(1024)
        cfg.backend_hostkey = RSAKey.generate(1024)
        cfg.host = "127.0.0.1"
        cfg.port = 12345
        cls.ingress = queue.Queue()
        cls.egress = queue.Queue()
        cls.connector = BackendConnector()
        endpoint = BackendConnector.EndPoint(ingress=cls.ingress,
                egress=cls.egress)
        cls.connector.register(endpoint)
        cls.connector.start()

    @classmethod
    def tearDownClass(cls):
        cls.connector.stop()
        cls.server_end.set()
        cls.server_thread.join()
        cls.server_sock.close()

    def test_backend_connector(self):
        self.server_ready.wait()
        msg = AddUserMessage(username="test_user", sudo=False)
        self.assertTrue(self.connector.is_active())
        self.egress.put(msg)

        reply = self.ingress.get(timeout=10)
        self.assertIsNotNone(reply)
        self.assertIsInstance(reply, FeedbackMessage)
        self.assertEqual(msg.mid, reply.mid)
        errmsg = "{} != {}: {}".format(reply.status, FeedbackMessage.SUCCESS,
                reply.feedback)
        self.assertEqual(reply.status, FeedbackMessage.SUCCESS, msg=errmsg)

    @classmethod
    def __server(cls):
        cfg = GlobalConfigStore()
        client, addr = cls.server_sock.accept()
        t = paramiko.Transport(client)
        t.add_server_key(cfg.backend_hostkey)
        t.set_subsystem_handler(cls.connector.Subsystem, SSHSubsystem)
        t.start_server(server=SSHServer())

        chan = t.accept(20)
        cls.server_ready.set()
        cls.server_end.wait()
        if chan:
            chan.close()
        t.close()

tests = [
        TestBackendConnector,
        ]

