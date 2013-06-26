# Copyright 2013 Databracket LLC
# See LICENSE file for details.

"""
:module: bastio.ssh.api
:synopsis: A module responsible for the API between the backend and the agent.
:author: Amr Ali <amr@databracket.com>

.. autoclass:: Processor
    :members:
"""

__author__ = "Amr Ali"
__copyright__ = "Copyright 2013 Databracket LLC"
__license__ = "GPLv3+"

import os
import pwd
import threading
import subprocess
import collections
import Queue as queue

from bastio.log import Logger
from bastio.mixin import KindSingletonMeta, public
from bastio.configs import GlobalConfigStore
from bastio.concurrency import GlobalThreadPool, Task
from bastio.ssh.client import BackendConnector
from bastio.ssh.protocol import (FeedbackMessage, AddUserMessage,
        RemoveUserMessage, UpdateUserMessage, AddKeyMessage, RemoveKeyMessage)

@public
class Processor(object):
    """A class to handle action messages coming from the backend and send back
    a feedback to indicate success or failure of the action requested. This class
    is a kind-singleton which means you cannot instantiate more than one copy per
    application life time.
    """
    __metaclass__ = KindSingletonMeta

    def __init__(self):
        self._tp = GlobalThreadPool()
        self._logger = Logger()
        self._ingress = queue.Queue()
        self._egress = queue.Queue()
        # TODO: Put the following in a configuration file.
        self._home_dir = '/home'
        self._user_dir = os.path.join(self._home_dir, '{username}')
        self._ssh_dir = os.path.join(self._user_dir, '.ssh')
        self._authkeys = os.path.join(self._ssh_dir, 'authorized_keys')
        # Start the action handler
        t = Task(target=self.__action_handler, infinite=True)
        t.failure = self.__catch_fail
        self._action_handler_task = self._tp.run(t)

    def endpoint(self):
        """Return an ingress and an egress points to communicate with this
        processor.

        :returns:
            :class:`bastio.ssh.client.BackendConnector.EndPoint`
        """
        return BackendConnector.EndPoint(ingress=self._ingress, egress=self._egress)

    def process(self, message):
        """Process a message and return a feedback.

        :param message:
            A message to be processed.
        :type message:
            A subclass of :class:`bastio.ssh.protocol.ActionMessage`
        :returns:
            :class:`bastio.ssh.protocol.FeedbackMessage`
        """
        if isinstance(message, AddUserMessage):
            # Add a user if one doesn't exist
            feedback = self._add_user(message)
        elif isinstance(message, RemoveUserMessage):
            # Remove a user if one exists
            feedback = self._remove_user(message)
        elif isinstance(message, UpdateUserMessage):
            # Update a user either to give it root access or to demote it
            feedback = self._update_user(message)
        elif isinstance(message, AddKeyMessage):
            # Add public key to the user's authorized_keys file
            feedback = self._add_key(message)
        elif isinstance(message, RemoveKeyMessage):
            # Remove public key from the user's authorized_keys file
            feedback = self._remove_key(message)
        else:
            # NOTE: This execution branch must never be reached,
            # do not take this lightly if it happens.
            feedback = message.reply(
                    ("internal error: agent does not know how to handle messages"
                        " of type `{type}`").format(type=message.type),
                    FeedbackMessage.ERROR)
        return feedback

    def stop(self):
        """Signal the action handler to stop."""
        self._action_handler_task.stop()

    def __action_handler(self, kill_ev):
        self._logger.warning("action handler started")
        while not kill_ev.is_set():
            message = self._get_ingress(timeout=3)
            if message:
                feedback = self.process(message)
                self._put_egress(feedback)

    def __catch_fail(self, failure):
        try:
            raise failure.exception, failure.message, failure.traceback
        except Exception:
            self._logger.critical("unexpected error occurred in the action handler",
                    exc_info=True)

    def _get_ingress(self, timeout):
        try:
            return self._ingress.get(timeout=timeout)
        except queue.Empty:
            return None

    def _put_egress(self, item):
        self._egress.put(item)

###
###  BEGIN COMMAND METHODS
###

    def _chk_user(self, message, status=FeedbackMessage.ERROR, should_exist=False):
        # Check if a user exists
        user_exist = os.path.exists(self._user_dir.format(
            username=message.username))
        try:
            pwd.getpwnam(message.username)
        except KeyError:
            user_exist = False

        if user_exist:
            reply_msg = "{username} already exists".format(username=message.username)
            if should_exist: # user exists and should
                return False
            else: # user exists but shouldn't
                feedback = message.reply(reply_msg, status)
        else:
            reply_msg = "{username} does not exist".format(username=message.username)
            if should_exist: # user doesn't exist but should
                feedback = message.reply(reply_msg, status)
            else: # user doesn't exist and shouldn't
                return False
        return feedback

    def _chk_key(self, message):
        # Check if a public key exists
        try:
            with open(self._authkeys.format(username=message.username), 'rb') as fd:
                auth_data = fd.read()
        except Exception:
            return False
        return message.public_key in auth_data

    def _create_ssh(self, message):
        # Make sure that .ssh exists and has the right permissions
        try:
            os.mkdir(self._ssh_dir.format(username=message.username), 0700)
        except OSError:
            pass # Directory already exists (or perm denied... very unlikely)

        # Touch .ssh/authorized_keys file
        auth_file = self._authkeys.format(username=message.username)
        try:
            with open(auth_file, 'ab') as fd:
                pass # We just want to create the file if it doesn't exist
        except IOError:
            # We can't do anything about it here, it will be handled by other messages
            pass

        # Make sure that .ssh/authorized_keys file has the right permissions
        try:
            os.chmod(auth_file, 0600)
        except OSError:
            # We can't do anything about it here, offload it to future messages
            pass

        # Chown .ssh/authorized_keys to the user
        try:
            pw_struct = pwd.getpwnam(message.username)
            os.chown(self._ssh_dir.format(username=message.username),
                    pw_struct.pw_uid, pw_struct.pw_gid)
            os.chown(auth_file, pw_struct.pw_uid, pw_struct.pw_gid)
        except KeyError:
            # username not found from getpwnam
            pass
        except OSError:
            # chown failed
            pass

    def _add_user(self, message):
        # Add user
        if message.sudo:
            add_command = 'useradd -mU -G sudo {username}'
        else:
            add_command = 'useradd -mU {username}'
        add_command = add_command.format(username=message.username)

        # Check if a user exists
        feedback = self._chk_user(message, FeedbackMessage.INFO, False)
        if feedback:
            self._create_ssh(message)
            return feedback

        # Create the user
        _, stderr = self._run_command(add_command)
        if stderr:
            feedback = message.reply(stderr, FeedbackMessage.ERROR)
            return feedback

        # Clear out user's password
        _, stderr = self._run_command("passwd -d {username}".format(
            username=message.username))
        if stderr:
            feedback = message.reply(stderr, FeedbackMessage.ERROR)
            return feedback

        self._create_ssh(message)
        feedback = message.reply("{username} was created successfully".format(
            username=message.username), FeedbackMessage.SUCCESS)
        return feedback

    def _remove_user(self, message):
        # Remove user
        rm_command = 'userdel -r {username}'.format(username=message.username)

        # Check if a user exists
        feedback = self._chk_user(message, FeedbackMessage.INFO, True)
        if feedback:
            return feedback

        # Try to remove the user
        _, stderr = self._run_command(rm_command)
        if stderr:
            feedback = message.reply(stderr, FeedbackMessage.ERROR)
        else:
            feedback = message.reply(
                    "{username} was removed successfully".format(
                        username=message.username), FeedbackMessage.SUCCESS)
        return feedback

    def _update_user(self, message):
        # Update user
        flag = '-a' if message.sudo else '-d'
        update_command = 'gpasswd {flag} {username} sudo'.format(flag=flag,
                username=message.username)

        # Check if a user exists
        feedback = self._chk_user(message, FeedbackMessage.ERROR, True)
        if feedback:
            return feedback

        # Update a user either to give it root access or to demote it
        _, stderr = self._run_command(update_command)
        if stderr:
            feedback = message.reply(stderr, FeedbackMessage.ERROR)
        else:
            if message.sudo:
                fb_str = '{username} was added to the sudo group successfully'
            else:
                fb_str = '{username} was removed from the sudo group successfully'
            feedback = message.reply(fb_str.format(username=message.username),
                    FeedbackMessage.SUCCESS)
        return feedback

    def _add_key(self, message):
        # Add public key
        pubkey = message.public_key
        username = message.username

        # Check if a user exists
        feedback = self._chk_user(message, FeedbackMessage.ERROR, True)
        if feedback:
            return feedback

        # Check if public key already exists
        if self._chk_key(message):
            feedback = message.reply(
                    "public key `{pub_key}` for {username} already exists".format(
                        pub_key=pubkey, username=username),
                    FeedbackMessage.INFO)
            return feedback

        # Try to add the public key to the user's authorized_keys file
        auth_file = self._authkeys.format(username=username)
        try:
            with open(auth_file, 'ab') as fd:
                fd.write(pubkey + '\n')
            feedback = message.reply(
                    "added public key to {username} successfully".format(
                        username=username), FeedbackMessage.SUCCESS)
        except IOError as ex:
            feedback = message.reply(ex.strerror, FeedbackMessage.ERROR)
        except Exception as ex:
            feedback = message.reply(ex.message, FeedbackMessage.ERROR)
        return feedback

    def _remove_key(self, message):
        # Remove public key
        pubkey = message.public_key
        username = message.username

        # Check if a user exists
        feedback = self._chk_user(message, FeedbackMessage.ERROR, True)
        if feedback:
            return feedback

        # Check if public key does not exist
        if not self._chk_key(message):
            feedback = message.reply(
                    "public key for {username} does not exist".format(
                        username=username), FeedbackMessage.INFO)
            return feedback

        # Try to remove the public key from the user's authorized_keys file
        auth_data = []
        auth_file = self._authkeys.format(username=username)
        try:
            with open(auth_file, 'rb') as fd:
                for line in fd.readlines():
                    if pubkey in line:
                        continue
                    auth_data.append(line)
            with open(auth_file, 'wb') as fd:
                # TODO: A race condition is possible here where the file could
                # be written to before we write to it and therefore overriding
                # the changes made to it by some other application. Find a fix
                # for it. This is quite unlikely in this particular case so
                # don't sweat it.
                fd.writelines(auth_data)
            feedback = message.reply(
                    "removed public key from {username} successfully".format(
                        username=username), FeedbackMessage.SUCCESS)
        except IOError as ex:
            feedback = message.reply(ex.strerror, FeedbackMessage.ERROR)
        except Exception as ex:
            feedback = message.reply(ex.message, FeedbackMessage.ERROR)
        return feedback

    @staticmethod
    def _run_command(command, input_data=None):
        try:
            po = subprocess.Popen(args=command, shell=True, stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = po.communicate(input_data)
        except OSError as ex:
            stderr = ex.strerror
        except ValueError as ex:
            stderr = ex.message
        return stdout, stderr

###
###  END COMMAND METHODS
###

