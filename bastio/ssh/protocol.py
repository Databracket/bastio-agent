# Copyright 2013 Databracket LLC
# See LICENSE file for details.

"""
:module: bastio.ssh.protocol
:synopsis: A module containing protocol messages.
:author: Amr Ali <amr@databracket.com>

.. rst-class:: html-toggle

Low Level Protocols
-------------------
.. autoclass:: Netstring
    :members:

.. rst-class:: html-toggle

Message Bases
-------------
.. autoclass:: ProtocolMessage
    :members:

.. autoclass:: ActionMessage
    :members:

.. rst-class:: html-toggle

Message Parsers
---------------
.. autoclass:: MessageParser
    :members:

.. autoclass:: ActionParser
    :members:

.. rst-class:: html-toggle

Protocol Messages
-----------------
.. autoclass:: FeedbackMessage
    :members:

.. autoclass:: AddUserMessage
    :members:

.. autoclass:: RemoveUserMessage
    :members:

.. autoclass:: UpdateUserMessage
    :members:

.. autoclass:: AddKeyMessage
    :members:

.. autoclass:: RemoveKeyMessage
    :members:
"""

__author__ = "Amr Ali"
__copyright__ = "Copyright 2013 Databracket LLC"
__license__ = "GPLv3+"

import re
import random

from bastio.mixin import Json, public
from bastio.ssh.crypto import RSAKey
from bastio.excepts import (BastioNetstringError, BastioEOFError,
        BastioMessageError, reraise)

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
                raise BastioNetstringError("non-digit character found in length part")
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
            str
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
            str
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
            raise BastioNetstringError("length specified does not match message length")
        if string[-1] != ',':
            raise BastioNetstringError("message terminator is missing")
        return data

@public
class ProtocolMessage(Json):
    """A protocol message base class."""

    def __init__(self, mid=None, **kwargs):
        super(ProtocolMessage, self).__init__()
        self.type = self.MessageType
        if not mid:
            # A new message construction, not a reply to a received message,
            # generate our own mid
            self.mid = self.__generate_mid()
        else:
            self.mid = mid
        self.parse(self, False)

    def reply(self, feedback, status):
        """Reply to a specific message with a feedback message that has
        the same MID.

        :param feedback:
            The feedback message string.
        :type feedback:
            str
        :param status:
            The status of the feedback message.
        :type status:
            int
        :returns:
            :class:`FeedbackMessage`
        """
        return FeedbackMessage(feedback, status, **self.__dict__)

    @classmethod
    def parse(cls, obj, traverse=True):
        """Check protocol message fields and validate them.

        Return a new object of type ``cls`` containing the validated
        feedback object.

        :param obj:
            A JSON object containing the relevant fields for this protocol message.
        :type obj:
            :class:`bastio.mixin.Json`
        :param traverse:
            Whether to traverse ``parse`` on all the classes in the hierarchy.
        :type traverse:
            bool
        :returns:
            A new object of type ``cls`` containing the validated protocol
            message object.
        """
        if 'mid' not in obj:
            raise BastioMessageError("message ID field is missing")
        if traverse:
            return cls(**obj.__dict__)

    @staticmethod
    def __generate_mid():
        return str(random.getrandbits(64))

@public
class FeedbackMessage(ProtocolMessage):
    """A protocol feedback message."""
    MessageType = "feedback"
    ERROR = 500
    WARNING = 400
    INFO = 300
    SUCCESS = 200
    STATUSES = [ERROR, WARNING, INFO, SUCCESS]

    def __init__(self, feedback, status, **kwargs):
        self.feedback = feedback
        self.status = status
        super(FeedbackMessage, self).__init__(**kwargs)
        self.parse(self, False)

    @classmethod
    def parse(cls, obj, traverse=True):
        """Check feedback message fields and validate them.

        Return a new object of type ``cls`` containing the validated
        feedback object.

        :param obj:
            A JSON object containing the relevant fields for this feedback message.
        :type obj:
            :class:`bastio.mixin.Json`
        :param traverse:
            Whether to traverse ``parse`` on all the classes in the hierarchy.
        :type traverse:
            bool
        :returns:
            A new object of type ``cls`` containing the validated feedback
            object.
        """
        if 'feedback' not in obj:
            raise BastioMessageError("feedback field is missing")
        if 'status' not in obj:
            raise BastioMessageError("status field is missing")
        if obj.status not in cls.STATUSES:
            raise BastioMessageError("status field is invalid")
        if traverse:
            return super(FeedbackMessage, cls).parse(obj)

@public
class ActionMessage(ProtocolMessage):
    """A protocol action message base class. Use this class as a base for all
    other action messages.
    """
    MessageType = 'action'

    def __init__(self, username, **kwargs):
        self.action = self.ActionType
        self.username = username
        super(ActionMessage, self).__init__(**kwargs)
        self.parse(self, False)

    @classmethod
    def parse(cls, obj, traverse=True):
        """Check action message fields and validate them.

        Return a new object of type ``cls`` containing the validated
        action object.

        :param obj:
            A JSON object containing the relevant fields for this action message.
        :type obj:
            :class:`bastio.mixin.Json`
        :param traverse:
            Whether to traverse ``parse`` on all the classes in the hierarchy.
        :type traverse:
            bool
        :returns:
            A new object of type ``cls`` containing the validated action
            object.
        """
        if 'username' not in obj:
            raise BastioMessageError("username field is missing")
        if not re.match("^([a-z_][a-z0-9_]{0,30})$", obj.username):
            raise BastioMessageError("username field is invalid")
        if traverse:
            return super(ActionMessage, cls).parse(obj)

@public
class AddUserMessage(ActionMessage):
    """An add-user action message."""
    ActionType = 'add-user'

    def __init__(self, sudo, **kwargs):
        self.sudo = sudo
        super(AddUserMessage, self).__init__(**kwargs)
        self.parse(self, False)

    @classmethod
    def parse(cls, obj, traverse=True):
        """Check add-user message fields and validate them.

        Return a new object of type ``cls`` containing the validated
        action object.

        :param obj:
            A JSON object containing the relevant fields for this action message.
        :type obj:
            :class:`bastio.mixin.Json`
        :param traverse:
            Whether to traverse ``parse`` on all the classes in the hierarchy.
        :type traverse:
            bool
        :returns:
            A new object of type ``cls`` containing the validated action
            object.
        """
        if 'sudo' not in obj:
            raise BastioMessageError("sudo field is missing")
        if traverse:
            return super(AddUserMessage, cls).parse(obj)

@public
class RemoveUserMessage(ActionMessage):
    """A remove-user action message."""
    ActionType = 'remove-user'

    def __init__(self, **kwargs):
        super(RemoveUserMessage, self).__init__(**kwargs)
        self.parse(self, False)

    @classmethod
    def parse(cls, obj, traverse=True):
        """Check remove-user message fields and validate them.

        Return a new object of type ``cls`` containing the validated
        action object.

        :param obj:
            A JSON object containing the relevant fields for this action message.
        :type obj:
            :class:`bastio.mixin.Json`
        :param traverse:
            Whether to traverse ``parse`` on all the classes in the hierarchy.
        :type traverse:
            bool
        :returns:
            A new object of type ``cls`` containing the validated action
            object.
        """
        if traverse:
            return super(RemoveUserMessage, cls).parse(obj)

@public
class UpdateUserMessage(ActionMessage):
    """A update-user action message."""
    ActionType = 'update-user'

    def __init__(self, sudo, **kwargs):
        self.sudo = sudo
        super(UpdateUserMessage, self).__init__(**kwargs)
        self.parse(self, False)

    @classmethod
    def parse(cls, obj, traverse=True):
        """Check update-user message fields and validate them.

        Return a new object of type ``cls`` containing the validated
        action object.

        :param obj:
            A JSON object containing the relevant fields for this action message.
        :type obj:
            :class:`bastio.mixin.Json`
        :param traverse:
            Whether to traverse ``parse`` on all the classes in the hierarchy.
        :type traverse:
            bool
        :returns:
            A new object of type ``cls`` containing the validated action
            object.
        """
        if 'sudo' not in obj:
            raise BastioMessageError("sudo field is missing")
        if traverse:
            return super(UpdateUserMessage, cls).parse(obj)

@public
class AddKeyMessage(ActionMessage):
    """A add-key action message."""
    ActionType = 'add-key'

    def __init__(self, public_key, **kwargs):
        self.public_key = public_key
        super(AddKeyMessage, self).__init__(**kwargs)
        self.parse(self, False)

    @classmethod
    def parse(cls, obj, traverse=True):
        """Check add-key message fields and validate them.

        Return a new object of type ``cls`` containing the validated
        action object.

        :param obj:
            A JSON object containing the relevant fields for this action message.
        :type obj:
            :class:`bastio.mixin.Json`
        :param traverse:
            Whether to traverse ``parse`` on all the classes in the hierarchy.
        :type traverse:
            bool
        :returns:
            A new object of type ``cls`` containing the validated action
            object.
        """
        if 'public_key' not in obj:
            raise BastioMessageError("public_key field is missing")
        if not RSAKey.validate_public_key(obj.public_key):
            raise BastioMessageError("public_key field is invalid")
        if traverse:
            return super(AddKeyMessage, cls).parse(obj)

@public
class RemoveKeyMessage(ActionMessage):
    """A remove-key action message."""
    ActionType = 'remove-key'

    def __init__(self, public_key, **kwargs):
        self.public_key = public_key
        super(RemoveKeyMessage, self).__init__(**kwargs)
        self.parse(self, False)

    @classmethod
    def parse(cls, obj, traverse=True):
        """Check remove-key message fields and validate them.

        Return a new object of type ``cls`` containing the validated
        action object.

        :param obj:
            A JSON object containing the relevant fields for this action message.
        :type obj:
            :class:`bastio.mixin.Json`
        :param traverse:
            Whether to traverse ``parse`` on all the classes in the hierarchy.
        :type traverse:
            bool
        :returns:
            A new object of type ``cls`` containing the validated action
            object.
        """
        if 'public_key' not in obj:
            raise BastioMessageError("public_key field is missing")
        if not RSAKey.validate_public_key(obj.public_key):
            raise BastioMessageError("public_key field is invalid")
        if traverse:
            return super(RemoveKeyMessage, cls).parse(obj)

@public
class ActionParser(object):
    """A protocol action message parser.

    Note that this class acts as a router for the actions that you can carry
    out, so in order to add support for a particular action you will have to
    edit the class dictionary ``SupportedActions`` to include the action type
    you wish to support.
    """
    MessageType = ActionMessage.MessageType
    SupportedActions = {
            AddUserMessage.ActionType: AddUserMessage,
            RemoveUserMessage.ActionType: RemoveUserMessage,
            UpdateUserMessage.ActionType: UpdateUserMessage,
            AddKeyMessage.ActionType: AddKeyMessage,
            RemoveKeyMessage.ActionType: RemoveKeyMessage,
            }

    @classmethod
    def parse(cls, obj):
        """Parse an action-type and return the relevant action object that
        represents the action-type of this message.

        :param obj:
            A JSON object for an action.
        :type obj:
            :class:`bastio.mixin.Json`
        :returns:
            A parsed and validated action message.
        """
        if 'action' not in obj:
            raise BastioMessageError("action field is missing")
        if obj.action not in cls.SupportedActions:
            raise BastioMessageError(
                    "action type `{}` is not supported".format(obj.action))
        return cls.SupportedActions[obj.action].parse(obj)

@public
class MessageParser(object):
    """A protocol message parser for JSON strings.

    Note that this class acts as a router for the type of messages you can
    handle, so in order to add support for another message you will have to
    edit the class dictionary ``SupportedMessages`` to include the message
    type you wish to support.
    """

    SupportedMessages = {
            FeedbackMessage.MessageType: FeedbackMessage,
            ActionParser.MessageType: ActionParser,
            }

    @classmethod
    def parse(cls, json_string):
        """Parse a JSON string and return the relevant object that represents
        the type of this message.

        :param json_string:
            The JSON string for a message.
        :type json_string:
            str
        :returns:
            An object that represents this message type.
        """
        try:
            obj = Json().from_json(json_string)
        except Exception:
            reraise(BastioMessageError)

        if 'type' not in obj:
            raise BastioMessageError("type field is missing")
        if obj.type not in cls.SupportedMessages:
            raise BastioMessageError(
                    "message type `{}` is not supported".format(obj.type))
        return cls.SupportedMessages[obj.type].parse(obj)

