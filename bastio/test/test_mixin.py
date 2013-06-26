# Copyright 2013 Databracket LLC
# See LICENSE file for details.

"""
:module: bastio.test.test_mixin
:synopsis: Unit tests for the mixin module.
:author: Amr Ali <amr@databracket.com>
"""

__author__ = "Amr Ali"
__copyright__ = "Copyright 2013 Databracket LLC"
__license__ = "GPLv3+"

import unittest
from bastio.mixin import KindSingletonMeta, UniqueSingletonMeta, Json

class KindTmpClass(object):
    __metaclass__ = KindSingletonMeta

    def __init__(self, name):
        self.name = name

class UniqueTmpClass(object):
    __metaclass__ = UniqueSingletonMeta

    def __init__(self, name):
        self.name = name

class TestSingleton(unittest.TestCase):
    def test_kind_singleton(self):
        test1 = KindTmpClass("test1")
        test2 = KindTmpClass("test2")
        self.assertEqual(test1.name, "test1")
        self.assertEqual(test2.name, test1.name)
        self.assertEqual(test1, test2)

    def test_unique_singleton(self):
        test1 = UniqueTmpClass("test1")
        test2 = UniqueTmpClass("test2")
        self.assertEqual(test1.name, "test1")
        self.assertEqual(test2.name, "test2")
        self.assertNotEqual(test2.name, test1.name)
        self.assertNotEqual(test1, test2)

class TestJson(unittest.TestCase):
    def test_json_mixin(self):
        obj = Json()
        obj.field_str = 'test'
        obj.field_int = 434
        obj.field_float = 4.34
        obj.field_sub = Json()
        obj.field_sub.field_str = 'sub_test'
        obj.field_sub.field_int = 123
        obj.field_sub.field_float = 1.23
        obj_json = Json().from_json(obj.to_json())
        self.assertEqual(obj_json.to_json(), obj.to_json())
        self.assertIn('field_str', obj_json)
        self.assertIsInstance(obj_json.field_str, basestring)
        self.assertIsInstance(obj_json.field_int, int)
        self.assertIsInstance(obj_json.field_float, float)
        self.assertIsInstance(obj_json.field_sub, Json)

        obj_json.field_fail = [Json()]
        with self.assertRaises(TypeError):
            obj_json.to_json()

tests = [
        TestSingleton,
        TestJson,
        ]

