# Copyright 2013 Databracket LLC
# See LICENSE file for details.

"""
:module: bastio.cli
:synopsis: A module responsible for the CLI of the agent.
:author: Amr Ali <amr@databracket.com>

.. autoclass:: CommandLine
    :members:

.. autofunction:: bastio_main
"""

__author__ = "Amr Ali"
__copyright__ = "Copyright 2013 Databracket LLC"
__license__ = "GPLv3+"

import os
import sys
import signal
import argparse

from bastio import __version__
from bastio.log import Logger
from bastio.mixin import public
from bastio.configs import GlobalConfigStore
from bastio.concurrency import GlobalThreadPool
from bastio.account import upload_public_key, download_backend_hostkey
from bastio.ssh.client import BackendConnector
from bastio.ssh.api import Processor
from bastio.ssh.crypto import RSAKey
from bastio.excepts import BastioConfigError

def __sig_handler(sig, frame):
    logger = Logger()
    logger.critical("signal received, shutting down")
    cfg = GlobalConfigStore()
    cfg.connector.stop()
    cfg.processor.stop()
    cfg.threadpool.remove_all_workers(3)

def _check_file_readability(filename):
    # Return a tuple of two status indicators, the first is to indicate that the
    # file exists and the second is an indication of file's readability.
    if not(filename and os.path.exists(filename)):
        return (False, False)
    try:
        with open(filename, 'rb') as fd:
            return (True, True)
    except Exception:
        return (True, False)

def _die(msg, success=False):
    if success:
        sys.stdout.write("{}\n".format(msg))
        sys.exit(0)
    else:
        sys.stderr.write("error: {}\n".format(msg))
        sys.exit(1)

@public
class CommandLine(object):
    """Parse and logically validate command line argments."""
    _description = "Bastio agent responsible for provisioning\n" \
            "system accounts."
    _epilog = "Report Bastio's bugs to support@bastio.com"

    def __init__(self):
        parser = argparse.ArgumentParser(description=self._description,
                formatter_class=argparse.RawDescriptionHelpFormatter,
                epilog=self._epilog)

        # Configure the command line parser

        # Miscellaneous arguments
        parser.add_argument('-c', '--config',
                help='configuration file path')
        parser.add_argument('--debug', action='store_true',
                help='run the agent in debugging mode where the logging will output to STDOUT')
        parser.add_argument('--version', action='version',
                version='%(prog)s ' + __version__,
                help='output version information and exit')
        parser.add_argument('-k', '--agent-key',
                help='path to the agent private key')

        # A group for commands that require start action details
        start_group = argparse.ArgumentParser(add_help=False)
        start_group.add_argument('-H', '--host', default='backend.bastio.com',
                help='host name of the Bastio backend (default: %(default)s)')
        start_group.add_argument('-p', '--port', type=int, default=2357,
                help='port of the backend to connect to (default: %(default)s)')
        start_group.add_argument('-m', '--min-threads', type=int, default=3,
                help='the minimum number of threads the thread pool must have (default: %(default)s)')
        start_group.add_argument('-s', '--stack-size', type=int, default=512,
                help='the stack size of each thread in KiB (default: %(default)sKiB)')

        # A group for commands that require account details
        api_group = argparse.ArgumentParser(add_help=False)
        api_group.add_argument('--api-key',
                help='Bastio API key')
        api_group.add_argument('-n', '--new-agent-key',
                help=('path to the new agent key to replace the old one specified by -k'
                    ' (this argument only make sense with `upload-key`)'))

        # A group for commands that require key details
        key_group = argparse.ArgumentParser(add_help=False)
        key_group.add_argument('--bits', type=int, default=2048,
                help=('number of bits to generate for the private key'
                    ' (default: %(default)s-bits, this argument only make sense with `generate-key`)'))

        # Command parsers
        sp = parser.add_subparsers(help='available commands', dest='command')
        sp.add_parser('generate-key', parents=[key_group],
                description=('Generate a new RSA private key and save it in the file '
                    'specified on the command line or in the configuration file.'),
                help='generate a new RSA private key for the agent')
        sp.add_parser('upload-key', parents=[api_group],
                description=('Extract the public key from the private key file '
                    'and upload it to Bastio server'),
                help='upload this agent public key')
        sp.add_parser('start', parents=[start_group, api_group],
                description='Start the agent in the foreground',
                help='start the agent')
        self.parser = parser

    def parse(self):
        """Parse and validate arguments from the command line and set
        global configurations.
        """
        self.args = self.parser.parse_args()
        cfg = GlobalConfigStore()
        cfg.prog = self.parser.prog
        cfg.debug = self.args.debug

        # Check of configuration file is available to us
        conf_avail = False
        if self.args.config:
            try:
                cfg.load(self.args.config)
                conf_avail = True
            except BastioConfigError as ex:
                self.parser.error(ex.message)

        # Check and validate agent's key if we are about to upload the key to
        # Bastio's servers or we are about to start the agent
        if self.args.command in ('upload-key', 'start'):
            # Get agent key file path from configuration file (if available)
            # or from the command line argument
            try:
                if conf_avail:
                    cfg.apikey = cfg.apikey if cfg.get_apikey else \
                            self.args.api_key
                    cfg.agentkey = cfg.agentkey if cfg.get_agentkey else \
                            self.args.agent_key
                else:
                    cfg.apikey = self.args.api_key
                    cfg.agentkey = self.args.agent_key
            except BastioConfigError as ex:
                _die(ex.message)
            # Check agent's key file readability and validate it
            res = _check_file_readability(cfg.agentkey)
            if not res[0]:
                self.parser.error('agent key file `{}` does not exist'.format(
                    cfg.agentkey))
            if not res[1]:
                self.parser.error(('permission to read the agent key file `{}` '
                    'is denied').format(cfg.agentkey))
            res = RSAKey.validate_private_key_file(cfg.agentkey)
            if not res:
                self.parser.error('agent key file `{}` is invalid'.format(
                    cfg.agentkey))

        # Parse and validate commands and their arguments
        if self.args.command == 'generate-key':
            try:
                if conf_avail:
                    cfg.agentkey = cfg.agentkey if cfg.get_agentkey else \
                            self.args.agent_key
                else:
                    cfg.agentkey = self.args.agent_key
                cfg.bits = self.args.bits
            except BastioConfigError as ex:
                _die(ex.message)
        elif self.args.command == 'upload-key':
            try:
                # Check new key file's readability and validate it if provided
                new_key = self.args.new_agent_key
                if new_key:
                    res = _check_file_readability(new_key)
                    if not res[0]:
                        self.parser.error(
                                'new agent key file `{}` does not exist'.format(
                                    new_key))
                    if not res[1]:
                        self.parser.error((
                                'permission to read the new agent key file `{}` '
                                'is denied').format(new_key))
                    res = RSAKey.validate_private_key_file(new_key)
                    if not res:
                        self.parser.error(
                                'new agent key file `{}` is invalid'.format(
                                    new_key))
                    cfg.new_agentkey = new_key
            except BastioConfigError as ex:
                _die(ex.message)
        elif self.args.command == 'start':
            try:
                if conf_avail:
                    cfg.host = cfg.host if cfg.get_host else self.args.host
                    cfg.port = cfg.port if cfg.getint_port else self.args.port
                    cfg.stacksize = cfg.stacksize if cfg.getint_stacksize else \
                            self.args.stack_size
                    cfg.minthreads = cfg.minthreads if cfg.getint_minthreads else \
                            self.args.min_threads
                else:
                    cfg.host = self.args.host
                    cfg.port = self.args.port
                    cfg.stacksize = self.args.stack_size
                    cfg.minthreads = self.args.min_threads
            except BastioConfigError as ex:
                _die(ex.message)
        else:
            # NOTE: This execution branch is blocked by argparse
            # so it is here only to account for extremely unlikely cases
            _die("unsupported command `{}`".format(self.args.command))
        return self.args.command

@public
def bastio_main():
    """Main application entry point."""
    signal.signal(signal.SIGINT, __sig_handler)
    signal.signal(signal.SIGTERM, __sig_handler)
    cfg = GlobalConfigStore()

    # Parse command line arguments
    cmd = CommandLine()
    command = cmd.parse()

    if command == 'generate-key':
        try:
            key = RSAKey.generate(cfg.bits)
            key.write_private_key_file(cfg.agentkey)
        except Exception as ex:
            _die(ex.message)
        _die("generated {}-bit key successfully".format(cfg.bits), True)
    elif command == 'upload-key':
        try:
            agentkey = RSAKey.from_private_key_file(cfg.agentkey)
        except Exception as ex:
            _die(ex.message)

        try:
            # Replace old key
            if cfg.new_agentkey:
                new_agentkey = RSAKey.from_private_key_file(cfg.new_agentkey)
                upload_public_key(cfg.apikey, new_agentkey.get_public_key(),
                        agentkey.get_public_key())
            else:
                upload_public_key(cfg.apikey, agentkey.get_public_key())
        except Exception as ex:
            _die(ex.message)
        _die("uploaded public key successfully", True)
    elif command == 'start':
        try:
            cfg.agent_username = cfg.apikey
            cfg.agentkey = RSAKey.from_private_key_file(cfg.agentkey)
            cfg.backend_hostkey = download_backend_hostkey()
        except Exception as ex:
            _die(ex.message)

    ### All that is below is part of the ``start`` command

    # Set logging based on debug status
    if cfg.debug:
        Logger().enable_stream()
    else:
        Logger().enable_syslog()

    cfg.threadpool = GlobalThreadPool(cfg.minthreads)
    cfg.processor = Processor()
    cfg.connector = BackendConnector()
    cfg.connector.register(cfg.processor.endpoint())
    cfg.connector.start()
    signal.pause()

