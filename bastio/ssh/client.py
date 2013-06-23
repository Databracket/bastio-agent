# Copyright 2013 Databracket LLC
# See LICENSE file for details.

"""
:module: bastio.ssh.client
:synopsis: A module for SSH client implementations.
:author: Amr Ali <amr@databracket.com>

.. autoclass:: BackendConnector
    :members:
"""

__author__ = "Amr Ali"
__copyright__ = "Copyright 2013 Databracket LLC"
__license__ = "GPLv3+"

import time
import socket
import paramiko
import collections
import Queue as queue

from bastio import __version__
from bastio.log import Logger
from bastio.mixin import KindSingletonMeta, public
from bastio.configs import GlobalConfigStore
from bastio.concurrency import GlobalThreadPool, Task
from bastio.ssh.protocol import Netstring, MessageParser, ProtocolMessage
from bastio.excepts import (BastioBackendError, BastioEOFError,
        BastioNetstringError, BastioMessageError, reraise)

# Set paramiko client ID
paramiko.Transport._CLIENT_ID = "bastio-{}".format(__version__)

@public
class BackendConnector(object):
    """A singleton to establish and maintain a secure connection with the backend
    over a specific subsystem channel. This connector supports registering of
    endpoints where processors can register their endpoint to communicate with
    the backend. It is guaranteed that the messages will be delivered ASAP but
    the actual ETA is chaotic.
    """
    __metaclass__ = KindSingletonMeta
    EndPoint = collections.namedtuple("EndPoint", "ingress egress")
    Subsystem = 'bastio-agent'

    def __init__(self):
        cfg = GlobalConfigStore()
        self._tp = GlobalThreadPool()
        self._username = cfg.agent_username
        self._agent_key = cfg.agentkey
        self._backend_addr = (cfg.host, cfg.port)
        self._backend_hostkey = cfg.backend_hostkey
        self._logger = Logger()
        self._endpoints = []
        self._tx = queue.Queue()
        self._conn_handler_task = None
        self._connected = False
        self._running = False
        self._client = None
        self._chan = None

    def start(self):
        """Start the connection handler thread."""
        if not self._running:
            self._running = True
            t = Task(target=self.__conn_handler, infinite=True)
            t.failure = self._catch_fail
            self._conn_handler_task = self._tp.run(t)

    def stop(self):
        """Stop the connection handler thread."""
        if self._running:
            self._running = False
            self.close()
            self._conn_handler_task.stop()

    def register(self, endpoint):
        """Register an endpoint to this connector to so that it can communicate
        with the backend. The endpoint is a tuple of one ingress queue as first
        argument and egress as the second argument.

        :param endpoint:
            A tuple of two queues; ingress and egress.
        :type endpoint:
            :class:`BackendConnector.EndPoint`
        """
        self._endpoints.append(endpoint)

    def is_active(self):
        """Check whether the transport is still active."""
        if self._client:
            t = self._client.get_transport()
            if t:
                return t.is_active()
        return False

    def close(self):
        """Close open channels and transport."""
        if self._chan:
            self._chan.close()
        if self._client:
            self._client.close()
        self._connected = False
        self._logger.critical("connection lost with the backend")

    def __conn_handler(self, kill_ev):
        self._logger.warning("backend connection handler started")
        while not kill_ev.is_set():
            # Try to connect to the backend
            try:
                self._connect()
            except BastioBackendError as ex:
                self.close()
                self._logger.critical(ex.message)
                # TODO: Implement a more decent reconnection strategy
                time.sleep(5) # Sleep 5 seconds before retrial
                continue

            # Read a message from the wire, parse it, and push it to ingress queue(s)
            try:
                json_string = self._read_message()
                message = MessageParser.parse(json_string)
                self._put_ingress(message)
            except socket.timeout:
                pass # No messages are ready to be read
            except BastioNetstringError as ex:
                self._logger.critical(
                        "error parsing a Netstring message: {}".format(ex.message))
                self.close()
                continue
            except BastioMessageError as ex:
                self._logger.critical(
                        "error parsing a protocol message: {}".format(ex.message))
                self.close()
                continue
            except BastioEOFError:
                self._logger.critical("received EOF on channel")
                self.close()
                continue

            # Get an item from the egress queue(s) and send it to the backend
            try:
                message = self._get_egress(timeout=0.01) # 10ms
                if message == None:
                    # No message is available to send
                    continue
                self._write_message(message.to_json())
            except socket.timeout:
                # Too many un-ACK'd packets? Sliding window shut on our fingers?
                # We don't really know what happened, lets reschedule the last
                # message for retransmission anyway
                self._push_queue(self._tx, message)
            except BastioEOFError:
                # Message was not sent because channel was closed
                # re-push the message to the TX queue again and retry connection
                self._push_queue(self._tx, message)
                self.close()
                continue

    def _connect(self):
        """An idempotent method to connect to the backend."""
        try:
            if self._connected:
                return
            # Prepare host keys
            self._client = paramiko.SSHClient()
            hostkeys = self._client.get_host_keys()
            hostkey_server_name = self._make_hostkey_entry_name(self._backend_addr)
            hostkeys.add(hostkey_server_name, self._backend_hostkey.get_name(),
                    self._backend_hostkey)

            # Try to connect
            self._client.connect(hostname=self._backend_addr[0],
                    port=self._backend_addr[1], username=self._username,
                    pkey=self._agent_key, allow_agent=False,
                    look_for_keys=False)
            self._connected = True

            # Open session and establish the subsystem
            self._chan = self._invoke_bastio()
            self._logger.critical("connection established with the backend")
        except BastioBackendError:
            raise
        except paramiko.AuthenticationException:
            reraise(BastioBackendError, "authentication with backend failed")
        except paramiko.BadHostKeyException:
            reraise(BastioBackendError, "backend host key does not match")
        except socket.error as ex:
            reraise(BastioBackendError, ex.strerror.lower())
        except Exception:
            reraise(BastioBackendError)

    def _invoke_bastio(self):
        """Start a bastio subsystem on an already authenticated transport.

        :returns:
            A channel connected to the subsystem or None.
        """
        if not self.is_active():
            raise BastioBackendError("client is not connected")
        t = self._client.get_transport()
        chan = t.open_session()
        if not chan:
            raise BastioBackendError("opening a session with the backend failed")
        chan.settimeout(0.01) # 10ms
        chan.invoke_subsystem(self.Subsystem)
        return chan

    def _read_message(self):
        nets = Netstring(self._chan)
        return nets.recv()

    def _write_message(self, data):
        nets = Netstring.compose(data)
        remaining = len(nets)
        while remaining > 0:
            n = self._chan.send(nets)
            if n <= 0:
                raise BastioEOFError("channel closed")
            remaining -= n

    def _put_ingress(self, item):
        for endpoint in self._endpoints:
            endpoint.ingress.put(item)

    def _get_egress(self, timeout):
        for endpoint in self._endpoints:
            try:
                item = endpoint.egress.get_nowait()
                self._tx.put(item)
            except queue.Empty:
                pass
        try:
            return self._tx.get(timeout=timeout)
        except queue.Empty:
            return None

    @staticmethod
    def _catch_fail(failure):
        log = Logger()
        try:
            raise failure.exception, failure.message, failure.traceback
        except:
            msg = 'unexpected error occurred: {}'.format(failure.message)
            log.critical(msg, exc_info=True)

    @staticmethod
    def _make_hostkey_entry_name(addr):
        """We do the following to work around a paramiko inconsistency."""
        if addr[1] == paramiko.config.SSH_PORT:
            return addr[0]
        return '[{}]:{}'.format(*addr)

