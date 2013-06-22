# Copyright 2013 Databracket LLC
# See LICENSE file for details.

"""
:module: bastio.test.test_configs
:synopsis: Unit tests for the configs module.
:author: Amr Ali <amr@databracket.com>
"""

__author__ = "Amr Ali"
__copyright__ = "Copyright 2013 Databracket LLC"
__license__ = "GPLv3+"

import os
import unittest

from bastio.configs import GlobalConfigStore
from bastio.excepts import BastioConfigError

class TestGlobalConfigStore(unittest.TestCase):
    def setUp(self):
        self._conffile = 'TEST_CONFIG_FILE'
        confs = """[agent]
test_value = hello world
test_int = 434
[test]
test1_value = hello
test1_float = 44.3
        """
        file(self._conffile, 'wb').write(confs)

    def test_global_config_store(self):
        cfg = GlobalConfigStore()
        cfg.initialized = True
        self.assertEqual(cfg, GlobalConfigStore())
        self.assertTrue(cfg.initialized)
        self.assertTrue(GlobalConfigStore().initialized)
        self.assertEqual(cfg.initialized, GlobalConfigStore().initialized)

        # Test configuration file
        cfg.load(self._conffile)
        self.assertEqual(cfg.test_value, 'hello world')
        self.assertEqual(cfg.test_int, '434')
        self.assertEqual(cfg.get_agent_test_value, cfg.test_value)
        self.assertEqual(cfg.get_test_test1_value, 'hello')
        self.assertEqual(cfg.getfloat_test_test1_float, 44.3)

    def tearDown(self):
        os.unlink(self._conffile)

tests = [
        TestGlobalConfigStore,
        ]

