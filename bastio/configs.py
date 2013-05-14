# Copyright 2013 Databracket LLC
# See LICENSE file for details.

__author__ = "Amr Ali"
__copyright__ = "Copyright 2013 Databracket LLC"
__license__ = "GPLv3+"

"""
:module: bastio.configs
:synopsis: Configurations memory and file system store.
:author: Amr Ali <amr@databracket.com>

Configuration Store
-------------------
.. autoclass:: GlobalConfigStore
    :members:
    :special-members:
"""

import os
import ConfigParser

from collections import defaultdict

from bastio.mixin import public, UniqueSingletonMeta
from bastio.excepts import BastioConfigError, reraise

@public
class GlobalConfigStore(defaultdict):
    """An in-memory configuration store that inherits :class:`defaultdict`
    behavior. This store is a singleton so only one object is created.
    Please see :class:`bastio.mixins.UniqueSingletonMeta`.

    The in-memory store takes precedence over the configuration file. If key
    was not found in the memory store we'll try to get it from the configuration
    file, if all fails we will simply return the default value of the
    ``default_factory`` assigned in the constructor.
    """
    __metaclass__ = UniqueSingletonMeta

    def __init__(self, section='bastio-agent', default_factory=str):
        """
        :param section:
            The section of the configuration file to use by default.
        :type section:
            str
        :param default_factory:
            See :class:`collections.defaultdict`
        :type default_factory:
            object
        """
        super(GlobalConfigs, self).__init__(default_factory)
        self._section = section
        self._config = None

    def __getattr__(self, name):
        """
        There's only one case where precedence is reversed in favor of the
        configuration file; when one of the [method]s below are present right
        before the <option name>. This and once the value is retrieved successfully
        it will be set in the memory store so that you can access it later without
        having to consult the configuration file again.

        :param name:
            The syntax is [method]_[section]_<option name> where [method] and
            [section] are optional, and <option name> is required. Note that
            if you wish not to supply [method] you need to remove [section] and
            ``_`` as well. Also if [section] was not supplied the default section
            name that was supplied to the constructor will be used.

            [method] could be one of a few possibilities. Either ``get``,
            ``getint``, ``getfloat``, or ``getboolean`` that correspond to the
            methods available through the :class:`ConfigParser` interface.

            e.g., ``get_alpha_name`` will try to get the option ``name`` from
            the configuration file, similarly in the case of ``get_name`` we will
            try to get the option's value from the configuration file but from
            under the section that was supplied to the constructor.
        :type name:
            str
        :returns:
            The option's value or ``default_factory`` if no value was set.
        :raises:
            :class:`bastio.excepts.BastioConfigError`
        """
        if name.startswith('get'):
            tmp = name.split('_')
            method = tmp[0]

            # Check if the method requested is supported
            if not hasattr(self._config, method):
                raise BastioConfigError('method `{}` is not supported'.format(
                    method))

            # Check if <option name> was supplied
            if len(tmp) < 2:
                raise BastioConfigError(
                        'must supply an option name after the method `{}`'.format(
                            method))

            # Syntax is now assumed to be [method]_<option name>
            if len(tmp) == 2:
                method = tmp[0]
                option = '_'.join(tmp[1:])
                try:
                    self[option] = getattr(self._config, method)(self._section,
                            option)
                except ConfigParser.NoOptionError:
                    return self[option]
                except ConfigParser.Error:
                    reraise(BastioConfigError)
                return self[option]

            # Handle the case where [section] is also provided
            if len(tmp) > 2:
                method = tmp[0]
                section = tmp[1]
                option = '_'.join(tmp[2:]) # Treat the rest as the option name
                try:
                    self[option] = getattr(self._config, method)(section, option)
                except ConfigParser.NoOptionError:
                    return self[option]
                except ConfigParser.Error:
                    reraise(BastioConfigError)
                return self[option]
        else:
            if self._config:
                # Check if it exists in the memory store and if not try the
                # configuration file
                if name in self:
                    return self[name]

                # Now let's try the configuration file
                try:
                    self[option] = self._config.get(self._section, name)
                except ConfigParser.NoOptionError:
                    # Not found here either, return value of ``default_factory``
                    return self[name]
                except ConfigParser.Error:
                    reraise(BastioConfigError)
            return self[name]

    def __setattr__(self, name, value):
        """Set a value to the in-memory store.

        :param name:
            The key in the key-value in-memory store.
        :type name:
            str
        :param value:
            The value in the key-value in-memory store.
        :type value:
            object
        """
        self[name] = value

    def load(self, filename):
        """Load a configuration file using :class:`ConfigParser` into memory.

        :param filename:
            The absolute path of the configuration file.
        :type filename:
            str
        :raises:
            :class:`bastio.excepts.BastioConfigError`
        """
        if not os.path.exists(filename):
            raise BastioConfigError(
                    'configuration file `{}` does not exist'.format(filename))
        self._config = ConfigParser.SafeConfigParser()
        ret = self._config.read(filename)
        if not ret:
            raise BastioConfigError(
                    'could not load configuration file: `{}`'.format(filename))

