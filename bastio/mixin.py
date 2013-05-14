# Copyright 2013 Databracket LLC
# See LICENSE file for details.

__author__ = "Amr Ali"
__copyright__ = "Copyright 2013 Databracket LLC"
__license__ = "GPLv3+"

"""
:module: bastio.mixins
:synopsis: Mixins utilities used across the project.
:author: Amr Ali <amr@databracket.com>

Metaclasses
-----------
.. autoclass:: SingletonAbstractMeta

.. autoclass:: KindSingletonMeta

.. autoclass:: UniqueSingletonMeta

Data Structure Mixins
---------------------
.. autoclass:: Json
    :members:
"""

import json
from collections import defaultdict

from bastio.excepts import BastioUnimplementedError

def public(obj):
    """A decorator to avoid retyping function/class names in __all__."""
    import sys
    _all = sys.modules[obj.__module__].__dict__.setdefault('__all__', [])
    if obj.__name__ not in _all:
        _all.append(obj.__name__)
    return obj

class SingletonAbstractMeta(type):
    """A Singleton pattern abstract metaclass."""

    def __init__(cls, name, bases, attrs):
        super(SingletonAbstractMeta, cls).__init__(name, bases, attrs)
        cls._instance = defaultdict(str)

    def __call__(cls, *args, **kwargs):
        key = cls._make_key(*args, **kwargs)
        if key not in cls._instance:
            cls._instance[key] = super(SingletonAbstractMeta, cls).__call__(
                    *args, **kwargs)
        return cls._instance[key]

    @classmethod
    def _make_key(cls, *args, **kwargs):
        """A function responsible for generating a key to check against and see
        if an instance was already constructed for that key.

        This is an abstract function, it is required to override it.
        """
        raise BastioUnimplementedError("function _make_id is not implemented")

@public
class KindSingletonMeta(SingletonAbstractMeta):
    """A singleton pattern metaclass that uses the underlying class' name
    as the unique constraint.
    """

    @classmethod
    def _make_key(cls, *args, **kwargs):
        return cls.__class__

@public
class UniqueSingletonMeta(SingletonAbstractMeta):
    """A Singleton pattern metaclass that uses arguments passed to the
    underlying class constructor as the unique constraint.
    """

    @classmethod
    def _make_key(cls, *args, **kwargs):
        key = ''
        for arg in args:
            try:
                key += str(arg)
            except:
                continue
        for kwarg, value in kwargs.iteritems():
            try:
                key += str(kwarg) + str(value)
            except:
                continue
        return key

@public
class Json(object):
    """A mixin to give objects the ability to seralize and deseralize to/from
    JSON formatted string.
    """

    def to_json(self):
        """Serialize current object's members to a JSON formatted string.

        This function will only serialize members that don't start with ``_``
        or a ``callable``.

        :returns:
            A JSON formatted string.
        """
        import json
        from ast import literal_eval
        res = {}
        for key, value in self.__dict__.iteritems():
            if key.startswith('_') or callable(value):
                continue

            if isinstance(value, self.__class__):
                res.update({ key: literal_eval(value.toJson()) })
            else:
                res.update({ key: value })
        return json.dumps(res)

    def from_json(self, json_string):
        """Deserialize a JSON formatted string and populate the current object
        with members of the name and value provided in the JSON string.

        :returns:
            ``self``
        """
        import json
        obj = json.loads(json_string)
        for key, value in obj.iteritems():
            if isinstance(value, dict):
                self.__dict__[key] = Json()
                self.__dict__[key].__dict__.update(value)
            else:
                self.__dict__[key] = value
        return self
