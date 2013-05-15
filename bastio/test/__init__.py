import unittest
import test_concurrency
import test_mixin
import test_configs

def __make_suite(tests):
    suite = unittest.TestSuite()
    for test in tests:
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(test))
    return suite

suite = unittest.TestSuite()
suite.addTests(__make_suite(test_concurrency.tests))
suite.addTests(__make_suite(test_mixin.tests))
suite.addTests(__make_suite(test_configs.tests))

