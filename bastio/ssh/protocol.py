# Copyright 2013 Databracket LLC
# See LICENSE file for details.

__author__ = "Amr Ali"
__copyright__ = "Copyright 2013 Databracket LLC"
__license__ = "GPLv3+"

"""
:module: bastio.ssh.protocol
:synopsis: A module containing protocol messages.
:author: Amr Ali <amr@databracket.com>

Low Level Protocols
-------------------
.. autoclass:: Netstring
    :members:
"""

from bastio.mixin import public
from bastio.excepts import BastioNetstringError, BastioEOFError, reraise

@public
class Netstring(object):
    """A class to help parsing and composing Netstring formatted messages.

    This class takes a ``sock`` and an optional message length ``limit`` argument
    through its constructor for operating on data as it is received. The ``limit``
    parameter is in KiB, so passing ``limit=32`` means that the message length
    limit will be 32768 bytes. The socket passed must return a zero-sized string
    as an indication of EOF.

    There are two class methods, ``compose`` to compose Netstring formatted messages
    and ``parse`` to parse Netstring messages.
    """

    def __init__(self, sock, limit=32):
        self._sock = sock
        self._limit = limit * 1024

    def recv(self):
        """Receive a single Netstring message from the socket.

        :returns:
            The result of parsing a single Netstring message.
        """
        data_len = ''
        # Parse length part
        while True:
            char = self._sock.recv(1)
            if len(char) == 0:
                raise BastioEOFError("channel closed or EOF")
            data_len += char
            if data_len[-1] == ':':
                break
            elif not data_len[-1].isdigit():
                raise BastioNetstringError("non-digit chracter found in length part")
            elif int(data_len) > self._limit:
                raise BastioNetstringError("length part is bigger than the limit")
        try:
            data_len = int(data_len[:-1]) # Remove the extra ':'
        except ValueError:
            reraise(BastioNetstringError)
        data = self._sock.recv(data_len)
        if len(data) != data_len:
            raise BastioNetstringError("length specified does not match message length")
        if self._sock.recv(1) != ',':
            raise BastioNetstringError("message terminator is missing")
        return data

    @classmethod
    def compose(cls, data):
        """Compose a Netstring formatted message.

        :param data:
            The data to be wrapped in a Netstring message.
        :type data:
            ``str``
        :returns:
            A Netstring formatted message for the data passed in.
        """
        return str(len(data)) + ":" + data + ","

    @classmethod
    def parse(cls, string):
        """Parse a Netstring message and return the result.

        :param string:
            The Netstring message to be parsed.
        :type string:
            ``str``
        :returns:
            The result of parsing the Netstring message.
        """
        delim = string.find(':')
        if delim < 0:
            raise BastioNetstringError("unable to find length delimiter")
        elif delim == 0:
            raise BastioNetstringError("message length was not specified")

        try:
            length = int(string[:delim])
        except ValueError:
            reraise(BastioNetstringError)

        data = string[delim + 1:-1]
        if len(data) != length:
            raise BastioNetstringError("length specified does not match messsage length")
        if string[-1] != ',':
            raise BastioNetstringError("message terminator is missing")
        return data

